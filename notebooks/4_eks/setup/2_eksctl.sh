#!/usr/bin/env bash

echo "Installing Eksctl"
ARCH=amd64
PLATFORM=$(uname -s)_$ARCH

curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz"
tar -xzf eksctl_$PLATFORM.tar.gz -C /tmp && rm eksctl_$PLATFORM.tar.gz
sudo mv /tmp/eksctl /usr/local/bin

# Connect to our K8s
echo "Connecting to prod-eks-europe Kubernetes cluster"
aws eks update-kubeconfig --region eu-central-1 --name prod-eks-europe
kubectl config set-context --current --namespace=prod


echo "Testing kubectl commands"
echo "access to prod namespace: `kubectl auth can-i -n prod create pods`"
echo "access to dev  namespace: `kubectl auth can-i -n dev create pods`"
eksctl get nodegroup --cluster prod-eks-europe