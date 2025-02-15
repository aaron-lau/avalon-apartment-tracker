# Apartment Tracker

A serverless application that tracks apartment listings from Avalon Communities, specifically monitoring Avalon Willoughby Square and AVA DoBro in Brooklyn. The application checks for new listings and price changes daily, sending email notifications when changes are detected.

## Features

- Monitors apartment listings from multiple Avalon properties
- Filters for 1-bedroom apartments
- Tracks new listings and price changes
- Stores historical data in DynamoDB
- Sends email notifications via AWS SES
- Runs daily at 9:05 AM EST
- Calculates price per square foot for comparison

## Prerequisites

- AWS Account
- Python 3.13
- AWS CLI configured
- S3 bucket for deployment packages
- Verified email addresses in AWS SES

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aaron-lau/avalon-apartment-tracker.git
cd apartment-tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='us-east-1'
```

4. Update deployment variables:
```bash
export STACK_NAME="apartment-tracker-stack"
export BUCKET_NAME="your-bucket-name"
export ENVIRONMENT="dev"
export SENDER_EMAIL="your-verified@email.com"
export RECIPIENT_EMAIL="your@email.com"
```

## Deployment

Run the deployment script:
```bash
./deploy.sh
```

This will:
1. Create deployment packages
2. Upload packages to S3
3. Deploy/update the CloudFormation stack
4. Configure Lambda layers and function

## Infrastructure

The application uses several AWS services:
- Lambda: Runs the apartment tracking code
- DynamoDB: Stores apartment listing history
- CloudWatch Events: Schedules daily execution
- SES: Sends email notifications
- S3: Stores deployment packages
- IAM: Manages permissions

## Configuration

### CloudFormation Parameters

- `EnvironmentName`: Deployment environment (dev/prod)
- `TableReadCapacity`: DynamoDB read capacity units
- `TableWriteCapacity`: DynamoDB write capacity units
- `SenderEmail`: Verified SES sender email
- `RecipientEmail`: Notification recipient email
- `LambdaCodeBucket`: S3 bucket for deployment
- `LambdaCodeKey`: S3 key for function code
- `Layer1PackageKey`: S3 key for core dependencies
- `Layer2PackageKey`: S3 key for data processing dependencies

### Lambda Environment Variables

- `ENVIRONMENT`: Deployment environment
- `DYNAMODB_TABLE`: DynamoDB table name
- `SENDER_EMAIL`: Email sender address
- `RECIPIENT_EMAIL`: Email recipient address

## Usage

### Local Testing

Test the script locally:
```bash
python main.py --list-only
```

### Deployment Updates

Update the Lambda function:
```bash
./deploy.sh
```

### Manual Execution

Invoke the Lambda function manually:
```bash
aws lambda invoke \
  --function-name apartment-tracker-dev \
  --payload '{}' \
  response.json
```

## File Structure

```
apartment-tracker/
├── main.py              # Main application code
├── template.yaml        # CloudFormation template
├── deploy.sh           # Deployment script
├── requirements.txt    # Python dependencies
└── README.md          # Documentation
```

## Dependencies

Core dependencies:
- boto3
- requests
- urllib3

Data processing dependencies:
- pandas
- pyarrow
- numpy

## Monitoring

- CloudWatch Logs: `/aws/lambda/apartment-tracker-dev`
- DynamoDB: Check the ApartmentListings table
- CloudWatch Metrics: Lambda execution metrics

## Troubleshooting

Common issues and solutions:

1. Size limit exceeded:
   - Dependencies are split into two Lambda layers
   - Unnecessary files are removed during packaging

2. Import errors:
   - Check Lambda layer configuration
   - Verify package installation order

3. Permission issues:
   - Verify IAM role permissions
   - Check SES email verification status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Avalon Communities API
- AWS Documentation

## Future Improvements

- Add support for more properties
- Implement price trend analysis
- Add more filtering options

## Security

- AWS credentials are managed via IAM
- Sensitive data stored in environment variables
- Email sending restricted to verified addresses
- DynamoDB access limited to necessary operations

## Backup and Recovery

- DynamoDB table can be backed up using AWS Backup
- Code and configuration stored in version control
- Deployment packages preserved in S3
