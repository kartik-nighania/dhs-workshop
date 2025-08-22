import boto3
import dotenv
import os

print(dotenv.load_dotenv('./.env'))

def create_user_profile(domain_id, user_profile_name, execution_role_arn, aws_access_key_id, aws_secret_access_key, region_name):
    sagemaker_client = boto3.client(
        'sagemaker',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )

    response = sagemaker_client.create_user_profile(
        DomainId=domain_id,
        UserProfileName=user_profile_name,
        UserSettings={
            'ExecutionRole': execution_role_arn
        }
    )
    print(f"Created user profile: {user_profile_name}")

# Example usage
domain_id = "d-fqcyxrshr7ie"
execution_role_arn = "arn:aws:iam::050752632341:role/service-role/AmazonSageMaker-ExecutionRole-20241106T114968"

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'ap-south-1'

for i in range(2, 34):
    user_profile_name = f'user-{i}'
    create_user_profile(domain_id, user_profile_name, execution_role_arn, aws_access_key_id, aws_secret_access_key, region_name)

print("Done creating users")