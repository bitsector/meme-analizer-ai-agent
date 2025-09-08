#!/bin/bash

echo "Applying Terraform configuration with auto-approve..."
echo "Project ID: gcp-cloud-run-tests"
echo "Region: us-central1"
echo ""

# Initialize terraform if needed
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
fi

# Apply with auto-approve
echo "Running terraform apply with auto-approve..."
terraform apply -auto-approve -var="project_id=gcp-cloud-run-tests" -var="billing_account=" 

echo ""
echo "Terraform apply completed!"