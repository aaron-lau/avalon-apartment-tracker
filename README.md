# Apartment Tracker

A containerized serverless application that tracks apartment listings from Avalon Communities, specifically monitoring Avalon Willoughby Square and AVA DoBro in Brooklyn. The application checks for new listings and price changes daily, sending email notifications when changes are detected.


## Features

- Monitors apartment listings from multiple Avalon properties
- Filters for 1-bedroom apartments
- Tracks new listings and price changes
- Stores historical data in DynamoDB
- Sends email notifications via AWS SES
- Runs daily at 9:05 AM EST
- Calculates price per square foot for comparison
- Containerized deployment for consistent environments

## Prerequisites

- Python 3.13
- AWS Account
- Docker installed
- AWS CLI configured
- Verified email addresses in AWS SES
- ECR repository (created automatically by CloudFormation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aaron-lau/avalon-apartment-tracker.git
cd apartment-tracker
```

2. Create .env file for local testing:
```
cp .env.example .env

# Edit .env with your values:
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_REGION=us-east-1
# AWS_DEFAULT_REGION=us-east-1
# SENDER_EMAIL=your_sender@email.com
# RECIPIENT_EMAIL=your_recipient@email.com
# MIN_SQFT=650
```

3. Configure AWS credentials:
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_REGION='us-east-1'
```

4. Update deployment variables:
```bash
export STACK_NAME="apartment-tracker-stack"
export ENVIRONMENT="dev"
export SENDER_EMAIL="your-verified@email.com"
export RECIPIENT_EMAIL="your@email.com"
```

## Local Development
1. Build and run the container locally:
```
./test_local.sh
```

2. Test the function:
```
# Default (≥ 650 sqft)
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"list-only": true}'


# Custom minimum (e.g., ≥ 700 sqft)
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"list-only": true, "min-sqft": 700}'
```

3. View logs:
```
docker logs $(docker ps -q --filter ancestor=apartment-tracker)
```

## Deployment
1. Update deployment variables:
```
export STACK_NAME="apartment-tracker-stack"
export ENVIRONMENT="dev"
export SENDER_EMAIL="your-verified@email.com"
export RECIPIENT_EMAIL="your@email.com"
```

2. Deploy the application:
```
./deploy.sh
```

This will:
- Build the Docker image
- Push to ECR
- Deploy/update the CloudFormation stack
- Configure the Lambda function

## Infrastructure
The application uses several AWS services:

- Lambda: Runs the containerized application
- ECR: Stores the Docker image
- DynamoDB: Stores apartment listing history
- CloudWatch Events: Schedules daily execution
- SES: Sends email notifications
- IAM: Manages permissions

## File Structure

```
apartment-tracker/
├── main.py              # Main application code
├── Dockerfile          # Container configuration
├── template.yaml       # CloudFormation template
├── deploy.sh          # Deployment script
├── test_local.sh      # Local testing script
├── requirements.txt   # Python dependencies
├── .env.example       # Example environment variables
├── .gitignore        # Git ignore rules
└── README.md         # Documentation
```

## Configuration
### Environment Variables
Local testing (.env):

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `SENDER_EMAIL`: Verified SES sender email
- `RECIPIENT_EMAIL`: Notification recipient email

### CloudFormation Parameters
- `EnvironmentName`: Deployment environment (dev/prod)
- `TableReadCapacity`: DynamoDB read capacity
- `TableWriteCapacity`: DynamoDB write capacity
- `SenderEmail`: Verified SES sender email
- `RecipientEmail`: Notification recipient email
- `ECRRepositoryName`: Name for the ECR repository
- `ImageUri`: URI of the container image

## Monitoring
- CloudWatch Logs: /aws/lambda/apartment-tracker-dev
- DynamoDB: Check the ApartmentListings table
- CloudWatch Metrics: Lambda and container metrics
- ECR: Container image scanning results

## Troubleshooting
####
Container Issues:
```
# Check container logs
docker logs $(docker ps -q --filter ancestor=apartment-tracker)

# Inspect image
docker inspect apartment-tracker:latest

# Test container locally
docker run --env-file .env apartment-tracker
```

Deployment Issues:
```
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name apartment-tracker-stack

# Check Lambda logs
aws logs tail /aws/lambda/apartment-tracker-dev
```

## Security
- Container scanning enabled in ECR
- IAM roles with minimal permissions
- Environment variables for sensitive data
- No credentials in container images

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## Future Improvements

- Add support for more properties
- Implement price trend analysis
- Add web interface for viewing listings
- Include floor plan images
- Add more filtering options
- Implement container vulnerability scanning
- Add automated testing