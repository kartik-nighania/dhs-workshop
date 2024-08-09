#!/bin/bash
import boto3
import csv
from botocore.exceptions import ClientError
import uuid

iam = boto3.client('iam')

total_users = 60
group_name = 'llmops-workshop-attendee-group'
# Create the group if it doesn't exist
try:
    iam.get_group(GroupName=group_name)
    print(f"Group '{group_name}' already exists.")
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchEntity':
        iam.create_group(GroupName=group_name)
        print(f"Group '{group_name}' created.")
    else:
        raise

# Function to create a user and add to the group
def create_user(user_name):
    try:
        # Create the user
        iam.create_user(UserName=user_name)
        print(f"User '{user_name}' created.")

        # Add the user to the group
        iam.add_user_to_group(GroupName=group_name, UserName=user_name)
        print(f"User '{user_name}' added to group '{group_name}'.")

        # Create login profile for console access
        password = f"Pwd{str(uuid.uuid4())[:10]}123!" 
        iam.create_login_profile(UserName=user_name, Password=password, PasswordResetRequired=False)
        print(f"Login profile created for user '{user_name}'.")

        # Create access keys
        # access_key = iam.create_access_key(UserName=user_name)['AccessKey']
        # print(f"Access keys created for user '{user_name}'.")

        return {
            'Link': "https://009676737623.signin.aws.amazon.com/console",
            'UserName': user_name,
            'Password': password,
            # 'AccessKeyId': access_key['AccessKeyId'],
            # 'SecretAccessKey': access_key['SecretAccessKey']
        }
    except ClientError as e:
        print(f"Error creating user '{user_name}': {e}")
        return None

# List to store user credentials
user_credentials = []

# Create users and store their credentials
for i in range(1, total_users):
    user_name = f'user-{i}-llmops-workshop'
    credentials = create_user(user_name)
    if credentials:
        user_credentials.append(credentials)

# Write credentials to a CSV file
csv_file = 'user_credentials.csv'
with open(csv_file, 'w', newline='') as csvfile:
    fieldnames = ['Link', 'UserName', 'Password']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for user_cred in user_credentials:
        writer.writerow(user_cred)

print(f"User credentials have been written to '{csv_file}'.")