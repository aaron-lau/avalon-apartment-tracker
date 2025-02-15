#!/bin/bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='us-east-1'

export STACK_NAME="apartment-tracker-stack"
export BUCKET_NAME="your-bucket-name"
export ENVIRONMENT="dev"
export SENDER_EMAIL="your-verified@email.com"
export RECIPIENT_EMAIL="your@email.com"

# Create function package
mkdir -p function-package
cp main.py function-package/
cd function-package
zip -r ../function-package.zip .
cd ..

# Create Layer 1: Core dependencies
mkdir -p layer1-package/python
cd layer1-package/python
pip3 install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target . \
    boto3 requests urllib3

# Clean up unnecessary files
find . -type d -name "tests" -exec rm -rf {} +
find . -type d -name "__pycache__" -exec rm -rf {} +
cd ..
zip -r ../layer-package-1.zip python/
cd ..

# Create Layer 2: Data processing dependencies
mkdir -p layer2-package/python
cd layer2-package/python

# Install numpy first
pip3 install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target . \
    numpy

# Then install pandas and pyarrow
pip3 install \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target . \
    pandas pyarrow

# Clean up unnecessary files
find . -type d -name "tests" -exec rm -rf {} +
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.so" ! -name "_numpy_core.so" -delete
find . -type d -name "numpy/core/tests" -exec rm -rf {} +
find . -type d -name "numpy/testing" -exec rm -rf {} +
find . -type d -name "numpy/doc" -exec rm -rf {} +
cd ..
zip -r ../layer-package-2.zip python/
cd ..

# Upload to S3
aws s3 cp function-package.zip "s3://${BUCKET_NAME}/"
aws s3 cp layer-package-1.zip "s3://${BUCKET_NAME}/"
aws s3 cp layer-package-2.zip "s3://${BUCKET_NAME}/"


# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://apartment-tracker-stack.yaml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=${ENVIRONMENT} \
    ParameterKey=SenderEmail,ParameterValue=${SENDER_EMAIL} \
    ParameterKey=RecipientEmail,ParameterValue=${RECIPIENT_EMAIL} \
    ParameterKey=LambdaCodeBucket,ParameterValue=${BUCKET_NAME} \
    ParameterKey=LambdaCodeKey,ParameterValue=function-package.zip \
    ParameterKey=Layer1PackageKey,ParameterValue=layer-package-1.zip \
    ParameterKey=Layer2PackageKey,ParameterValue=layer-package-2.zip \
    ParameterKey=TableReadCapacity,ParameterValue=1 \
    ParameterKey=TableWriteCapacity,ParameterValue=1 \
    ParameterKey=UpdateTimestamp,ParameterValue=${TIMESTAMP} \
  --capabilities CAPABILITY_IAM

# Clean up
rm -rf function-package layer1-package layer2-package *.zip
