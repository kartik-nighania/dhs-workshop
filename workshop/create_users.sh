#!/bin/bash

policy_file="./policy.json"
policy_name="AV-workshop-user-access-policy"
group_name="AV-workshop-users"
credentials_directory="./credentials"

policy_arn=$(aws iam create-policy --policy-name $policy_name --policy-document file://$policy_file --query 'Policy.Arn' --output text)
echo "Policy ARN: $policy_arn"


aws iam create-group --group-name $group_name
echo "Group $group_name created."


aws iam attach-group-policy --group-name $group_name --policy-arn $policy_arn
echo "Policy $policy_name attached to group $group_name."

mkdir -p $credentials_directory
for i in $(seq 1 2); do
    user_name="av-user-${i}"
    aws iam create-user --user-name $user_name
    aws iam add-user-to-group --group-name $group_name --user-name $user_name
    aws iam create-access-key --user-name $user_name > "${credentials_directory}/${user_name}_credentials.json"
    echo "User $user_name created and added to $group_name. Credentials saved."
done

echo "All users created and configured."
