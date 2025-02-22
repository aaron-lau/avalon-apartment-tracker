FROM public.ecr.aws/lambda/python:3.13

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY main.py ${LAMBDA_TASK_ROOT}

# Set environment variables for local testing
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_REGION=${AWS_REGION}
ENV SENDER_EMAIL=${SENDER_EMAIL}
ENV RECIPIENT_EMAIL=${RECIPIENT_EMAIL}
ENV ENVIRONMENT=${ENVIRONMENT}

# Set the CMD to your handler
CMD [ "main.lambda_handler" ]