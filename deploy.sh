#!/bin/bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

export STACK_NAME="apartment-tracker-stack"
export ENVIRONMENT="dev"
export SENDER_EMAIL="your-verified@email.com"
export RECIPIENT_EMAIL="your@email.com"
export TIMESTAMP=$(date +%Y%m%d-%H%M%S)

export ECR_REPO_NAME="apartment-tracker"
export IMAGE_TAG="latest"

# Build Docker image
docker buildx build --platform linux/amd64 --provenance=false -t ${ECR_REPO_NAME}:${IMAGE_TAG} . --output type=docker

# Get ECR login token
aws ecr get-login-password --region ${AWS_REGION} | \
docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag image for ECR
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}

# Push image to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}

# Get image URI
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"

# Update or create CloudFormation stack
if aws cloudformation describe-stacks --stack-name ${STACK_NAME} 2>/dev/null; then
    echo "Updating existing stack..."
    aws cloudformation update-stack \
      --stack-name ${STACK_NAME} \
      --template-body file://${STACK_NAME}.yaml \
      --parameters \
        ParameterKey=EnvironmentName,ParameterValue=${ENVIRONMENT} \
        ParameterKey=SenderEmail,ParameterValue=${SENDER_EMAIL} \
        ParameterKey=RecipientEmail,ParameterValue=${RECIPIENT_EMAIL} \
        ParameterKey=ImageUri,ParameterValue=${IMAGE_URI} \
        ParameterKey=TableReadCapacity,ParameterValue=1 \
        ParameterKey=TableWriteCapacity,ParameterValue=1 \
        ParameterKey=ECRRepositoryName,ParameterValue=${ECR_REPO_NAME} \
        ParameterKey=UpdateTimestamp,ParameterValue=${TIMESTAMP} \
      --capabilities CAPABILITY_IAM

    # Wait for stack update to complete
    aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME}
else
    echo "Creating new stack..."
    aws cloudformation create-stack \
      --stack-name ${STACK_NAME} \
      --template-body file://${STACK_NAME}.yaml \
      --parameters \
        ParameterKey=EnvironmentName,ParameterValue=${ENVIRONMENT} \
        ParameterKey=SenderEmail,ParameterValue=${SENDER_EMAIL} \
        ParameterKey=RecipientEmail,ParameterValue=${RECIPIENT_EMAIL} \
        ParameterKey=ImageUri,ParameterValue=${IMAGE_URI} \
        ParameterKey=TableReadCapacity,ParameterValue=1 \
        ParameterKey=TableWriteCapacity,ParameterValue=1 \
        ParameterKey=ECRRepositoryName,ParameterValue=${ECR_REPO_NAME} \
        ParameterKey=UpdateTimestamp,ParameterValue=${TIMESTAMP} \
      --capabilities CAPABILITY_IAM

    # Wait for stack creation to complete
    aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME}
fi

echo "Deployment completed"
