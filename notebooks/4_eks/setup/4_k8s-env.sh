#!/bin/bash

export USER_NUMBER=5
# export AWS_REGION="us-east-1"
export AWS_REGION="ap-south-1"

export EKS_CLUSTER_NAME="av-demo-${USER_NUMBER}"

base_ip="10.42.0.0"

# Function to increment IP address
increment_ip() {
    local IFS=.
    local ip=($1)
    local plus=$2
    ((ip[3]+=plus))
    if ((ip[3] >= 256)); then
        ((ip[2]+=ip[3]/256))
        ((ip[3]%=256))
    fi
    echo "${ip[0]}.${ip[1]}.${ip[2]}.${ip[3]}"
}
subnet=$(increment_ip $base_ip $((16 * (USER_NUMBER - 1))))
export EKS_VPC_CIDR="${subnet}/28"
echo "User ${USER_NUMBER} CIDR: ${EKS_VPC_CIDR}"

# Create EKS Cluster
eksctl create cluster -f ./3_eks-cluster.yaml