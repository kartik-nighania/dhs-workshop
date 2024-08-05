#!/bin/bash

# Define the policy name
policy_name="FullAccessS3EC2SageMakerECR"

# Create the IAM policy using AWS CLI
aws iam create-policy \
    --policy-name "$policy_name" \
    --policy-document ./policy.json

echo "Policy $policy_name created successfully."