# Terraform Infrastructure for Agent Dolph Firebase Project

This Terraform configuration creates a complete Firebase project with Cloud Run backend infrastructure.

## Prerequisites

1. **Install required tools:**
   ```bash
   # Terraform
   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
   sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
   sudo apt-get update && sudo apt-get install terraform
   
   # Firebase CLI
   npm install -g firebase-tools
   
   # Google Cloud CLI
   curl https://sdk.cloud.google.com | bash
   ```

2. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   firebase login
   ```

3. **Get your billing account ID:**
   ```bash
   gcloud billing accounts list
   ```

## Deployment Steps

1. **Configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Plan the deployment:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## What This Creates

- **GCP Project** with Firebase enabled
- **Firebase Hosting** for frontend deployment
- **Cloud Run service** for backend API
- **Artifact Registry** for Docker images
- **IAM roles** and service accounts
- **Required APIs** enabled

## Next Steps

After Terraform completes:

1. Build and push your backend Docker image to Artifact Registry
2. Deploy Firebase Functions for your frontend
3. Configure Firebase Hosting

## Clean Up

To destroy all resources:
```bash
terraform destroy
```

**Note:** This will delete the entire project and all data!