import requests
import pandas as pd
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse

def send_email(subject, body):
    # Configure these with your verified SES emails
    SENDER = os.environ.get('SENDER_EMAIL')
    RECIPIENT = os.environ.get('RECIPIENT_EMAIL')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

    # Validate environment variables are set
    if not SENDER or not RECIPIENT:
        raise ValueError("SENDER_EMAIL and RECIPIENT_EMAIL environment variables must be set")

    # Create SES client
    ses_client = boto3.client('ses', region_name=AWS_REGION)
    
    # Create message
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = SENDER
    message["To"] = RECIPIENT

    # Add HTML body
    html_part = MIMEText(body, "html")
    message.attach(html_part)

    try:
        response = ses_client.send_raw_email(
            Source=SENDER,
            Destinations=[RECIPIENT],
            RawMessage={
                'Data': message.as_string()
            }
        )
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")


def get_listings(community_code, location_name, min_sqft=650):
    api_url = f"https://api.avalonbay.com/json/reply/ApartmentSearch?communityCode={community_code}"
    
    response = requests.get(api_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data for {location_name}. Status code: {response.status_code}")
    
    data = response.json()
    listings = {}
    
    # Check if we have available floor plan types
    available_floor_plans = data.get('results', {}).get('availableFloorPlanTypes', [])
    
    for floor_plan_type in available_floor_plans:
        # Skip if it's a studio floor plan type
        if floor_plan_type.get('value') == 0:
            continue

        for floor_plan in floor_plan_type.get('availableFloorPlans', []):
            for finish_package in floor_plan.get('finishPackages', []):
                for apartment in finish_package.get('apartments', []):
                    # Skip if apartment is smaller than minimum square footage
                    if apartment.get('apartmentSize', 0) < min_sqft:
                        continue

                    apt_number = apartment.get('apartmentNumber')
                    unique_id = f"{location_name}-{apt_number}"
                    
                    # Get pricing info
                    pricing = apartment.get('pricing', {})
                    effective_rent = pricing.get('effectiveRent')
                    
                    # Format move-in date
                    move_in_date = pricing.get('availableDate')
                    if move_in_date:
                        try:
                            date_obj = datetime.strptime(move_in_date, '%Y-%m-%dT%H:%M:%S')
                            move_in_date = date_obj.strftime('%b %d')
                        except ValueError:
                            pass
                    
                    # Get apartment details
                    sqft = apartment.get('apartmentSize')
                    floor = apartment.get('floor')
                    beds = apartment.get('beds')
                    baths = apartment.get('baths')
                    
                    # Get promotion info
                    has_promotion = apartment.get('hasPromotion', False)
                    promotion_amount = pricing.get('obAmount')
                    original_rent = pricing.get('amenitizedRent')
                    
                    listings[unique_id] = {
                        'location': location_name,
                        'apartment_name': apt_number,
                        'price': float(effective_rent if effective_rent is not None else 0),
                        'original_price': float(original_rent if original_rent is not None else 0),
                        'sqft': str(sqft),
                        'move_in_date': move_in_date,
                        'floor': floor,
                        'beds': beds,
                        'baths': baths,
                        'has_promotion': has_promotion,
                        'promotion_amount': promotion_amount,
                        'last_updated': datetime.now().isoformat()
                    }
    
    return listings

def print_current_listings(communities, min_sqft=650):
    all_listings = []
    
    for location_name, community_code in communities.items():
        try:
            location_listings = get_listings(community_code, location_name, min_sqft)
            for _, listing in location_listings.items():
                
                # Format promotion info
                price = listing['price']
                price_display = f"${price:,.2f}"
                if listing['has_promotion']:
                    price_display += f" (was ${listing['original_price']:,.2f})"
                
                # Calculate price per square foot
                try:
                    sqft = float(listing['sqft'])
                    price_per_sqft = price / sqft if sqft > 0 else 0
                    price_per_sqft_display = f"${price_per_sqft:.2f}"
                except (ValueError, TypeError):
                    price_per_sqft_display = "N/A"
                    price_per_sqft = float('inf')
                
                all_listings.append({
                    'Location': location_name,
                    'Apartment': listing['apartment_name'],
                    'Floor': listing['floor'],
                    'Price': price_display,
                    'Square Footage': listing['sqft'],
                    'Price/SqFt': price_per_sqft_display,
                    'Move-in Date': listing['move_in_date'],
                    '_sort_price_per_sqft': price_per_sqft
                })
        except Exception as e:
            print(f"Error fetching listings for {location_name}: {e}")
    
    # Convert to DataFrame and sort by price per sqft
    df = pd.DataFrame(all_listings)
    if not df.empty:
        df = df.sort_values('_sort_price_per_sqft').drop('_sort_price_per_sqft', axis=1)
        
        # Group by location and print
        for location in df['Location'].unique():
            location_df = df[df['Location'] == location]
            print(f"\n{location} Apartments Available (>= {min_sqft} sqft):")
            print("=" * 150)
            print(location_df.to_string(index=False))
            print("=" * 150)
            print(f"Total {location} apartments available: {len(location_df)}")
        
        print(f"\nTotal apartments available across all locations: {len(df)}")
    else:
        print(f"\nNo apartments found >= {min_sqft} sqft.")
        
def format_email_body(new_listings, price_changes):
    def sort_and_group_listings(listings):
        # Calculate price per sqft and sort
        for listing in listings:
            try:
                if 'price' in listing:
                    price = float(listing['price'].replace('$', '').replace(',', ''))
                else:
                    price = float(listing['new_price'].replace('$', '').replace(',', ''))
                sqft = float(listing['sqft'])
                listing['price_per_sqft'] = price / sqft
            except (ValueError, TypeError):
                listing['price_per_sqft'] = float('inf')

        # Group by location
        grouped = {}
        for listing in sorted(listings, key=lambda x: x['price_per_sqft']):
            location = listing['location']
            if location not in grouped:
                grouped[location] = []
            grouped[location].append(listing)
        
        return grouped

    email_body = "<h2>Apartment Updates</h2>"
    
    if new_listings:
        email_body += "<h3>New Listings:</h3>"
        grouped_new = sort_and_group_listings(new_listings)
        
        for location, listings in grouped_new.items():
            email_body += f"<h4>{location}</h4><ul>"
            for listing in listings:
                price_per_sqft = f"${listing['price_per_sqft']:.2f}/sqft" if listing['price_per_sqft'] != float('inf') else 'N/A'
                email_body += f"<li>Apt {listing['name']} - {listing['price']} - {listing['sqft']} sqft ({price_per_sqft}) - Move-in: {listing['move_in_date']}</li>"
            email_body += "</ul>"
    
    if price_changes:
        email_body += "<h3>Price Changes:</h3>"
        grouped_changes = sort_and_group_listings(price_changes)
        
        for location, changes in grouped_changes.items():
            email_body += f"<h4>{location}</h4><ul>"
            for change in changes:
                price_per_sqft = f"${change['price_per_sqft']:.2f}/sqft" if change['price_per_sqft'] != float('inf') else 'N/A'
                
                # Determine if price increased or decreased
                old_price = float(change['old_price'].replace('$', '').replace(',', ''))
                new_price = float(change['new_price'].replace('$', '').replace(',', ''))
                
                if new_price > old_price:
                    price_change_text = f"Price Increased to {change['new_price']} from {change['old_price']}"
                else:
                    price_change_text = f"Price Decreased to {change['new_price']} from {change['old_price']}"
                
                email_body += (
                    f"<li>Apt {change['name']} - {price_change_text} - "
                    f"{change['sqft']} sqft ({price_per_sqft}) - Move-in: {change['move_in_date']}</li>"
                )
            email_body += "</ul>"
    
    return email_body

def main(args=None):
    # Define communities and their codes
    communities = {
        'Willoughby': 'NY039',
        'Dobro': 'NY037',
        'Fort Greene': 'NY026'
    }

    parser = argparse.ArgumentParser(description='Apartment Listing Tracker')
    parser.add_argument('--list-only', action='store_true', 
                      help='Only print current listings without updating DynamoDB')
    parser.add_argument('--min-sqft', type=int, default=650,
                      help='Minimum square footage (default: 650)')
    
    # Parse arguments
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    if args.list_only:
        print(f"\nFiltering for apartments >= {args.min_sqft} sqft")
        print_current_listings(communities, args.min_sqft)
        return

    # Get current listings
    current_listings = {}
    for location_name, community_code in communities.items():
        try:
            location_listings = get_listings(community_code, location_name, args.min_sqft)
            current_listings.update(location_listings)
        except Exception as e:
            print(f"Error fetching listings for {location_name}: {e}")

    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = f"ApartmentListings-{os.environ.get('ENVIRONMENT')}"
    table = dynamodb.Table(table_name)
    
    # Get previous listings from DynamoDB
    previous_listings = {}
    try:
        response = table.scan()
        for item in response['Items']:
            previous_listings[item['apartment_id']] = {
                'location': item['location'],
                'apartment_name': item['apartment_name'],
                'price': float(item['price']),
                'sqft': item['sqft'],
                'move_in_date': item['move_in_date'],
                'last_updated': item['last_updated']
            }
    except Exception as e:
        print(f"Error reading from DynamoDB: {e}")
    
    # Compare and prepare notifications
    new_listings = []
    price_changes = []
    
    for apt_id, current_data in current_listings.items():
        # Update DynamoDB
        table.put_item(Item={
            'apartment_id': apt_id,
            'location': current_data['location'],
            'apartment_name': current_data['apartment_name'],
            'price': str(current_data['price']),
            'sqft': current_data['sqft'],
            'move_in_date': current_data['move_in_date'],
            'last_updated': current_data['last_updated']
        })
        
        if apt_id not in previous_listings:
            new_listings.append({
                'location': current_data['location'],
                'name': current_data['apartment_name'],
                'price': f"${current_data['price']:,.2f}",
                'sqft': current_data['sqft'],
                'move_in_date': current_data['move_in_date']
            })
        elif current_data['price'] != previous_listings[apt_id]['price']:
            price_changes.append({
                'location': current_data['location'],
                'name': current_data['apartment_name'],
                'old_price': f"${previous_listings[apt_id]['price']:,.2f}",
                'new_price': f"${current_data['price']:,.2f}",
                'sqft': current_data['sqft'],
                'move_in_date': current_data['move_in_date']
            })
    
    # Send email if there are updates
    if new_listings or price_changes:
        email_body = format_email_body(new_listings, price_changes)
        send_email("Apartment Listing Updates", email_body)
    else:
        print(f"No new listings today.")

        
def lambda_handler(event, context):
    # Get minimum square footage from environment variable
    min_sqft = int(os.environ.get('MIN_SQFT', 650))
    
    try:
        # Get minimum square footage from environment or event
        min_sqft = event.get('min-sqft', os.environ.get('MIN_SQFT', '650'))
        
        # Convert arguments to format expected by argparse
        args = []
        if event.get('list-only'):
            args.append('--list-only')
        args.extend(['--min-sqft', str(min_sqft)])

        main(args)
        return {
            'statusCode': 200,
            'body': 'Successfully processed apartment listings'
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error processing apartment listings: {str(e)}'
        }

if __name__ == "__main__":
    main()