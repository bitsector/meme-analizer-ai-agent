# Infrastructure Setup Guide

This document describes how to deploy and manage the meme-analyzer-ai-agent infrastructure.

## Architecture Overview

- **Backend**: Python FastAPI app running on Google Cloud Run
- **Frontend**: Static files hosted on Firebase Hosting  
- **Secrets**: Google Secret Manager (mounted as files in containers)
- **Images**: Google Artifact Registry
- **Infrastructure**: Terraform managed

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. Firebase CLI installed and authenticated  
3. Docker installed
4. Terraform installed
5. Secret file exists: `secrets/open_api_key.txt`

## Full Deployment (Day 1 or after terraform destroy)

### 1. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 2. Add Secret Value to Google Secret Manager
```bash
# Add the OpenAI API key to the secret
cat ../secrets/open_api_key.txt | gcloud secrets versions add open-api-key --data-file=-
```

### 3. Build and Push Backend Image
```bash
cd ..  # Back to project root

# Build backend image
docker build -f back/Dockerfile.back -t us-central1-docker.pkg.dev/gcp-cloud-run-tests/backend-images/agent-back:latest ./back

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/gcp-cloud-run-tests/backend-images/agent-back:latest
```

### 4. Update Cloud Run with New Image
```bash
cd terraform
terraform apply
```

### 5. Deploy Frontend (if needed)
```bash
cd ..  # Back to project root
firebase deploy --only hosting
```

## Daily Shutdown (Save Costs)

### Option 1: Scale to Zero (Recommended)
Edit `terraform/main.tf`, change the metadata annotations:
```hcl
metadata {
  annotations = {
    "autoscaling.knative.dev/maxScale" = "0"
    "autoscaling.knative.dev/minScale" = "0"
    "run.googleapis.com/cpu-throttling" = "false"
  }
}
```

Then apply:
```bash
cd terraform
terraform apply
```

### Option 2: Full Destroy
```bash
cd terraform
terraform destroy
```

Note: Firebase Hosting will continue running independently.

## Daily Startup

### If you used Scale to Zero:
Edit `terraform/main.tf`, change the metadata annotations back:
```hcl
metadata {
  annotations = {
    "autoscaling.knative.dev/maxScale" = "10"
    "run.googleapis.com/cpu-throttling" = "false"
  }
}
```

Then apply:
```bash
cd terraform
terraform apply
```

### If you used Full Destroy:
Follow the "Full Deployment" steps above.

## Local Development

Build and run locally with Docker Compose:
```bash
# Build and run both frontend and backend
docker compose down && \
docker build -f back/Dockerfile.back -t antonbiz/agent-back:1.0 ./back && \
docker build -f front/Dockerfile.front -t antonbiz/agent-front:1.0 ./front && \
docker compose up --build
```

## URLs

After deployment, your services will be available at:
- **Backend**: https://agent-backend-nfu3mwmvma-uc.a.run.app (check Terraform outputs)
- **Frontend**: https://your-firebase-project.web.app (check Firebase console)

## Terraform Outputs

To see all deployed resource URLs:
```bash
cd terraform
terraform output
```

## Troubleshooting

### Secret Not Found Error
Make sure you've added the secret value:
```bash
cat ../secrets/open_api_key.txt | gcloud secrets versions add open-api-key --data-file=-
```

### Docker Push Permission Denied
Authenticate Docker with Google Cloud:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Firebase Deploy Issues
Make sure you're authenticated and using the right project:
```bash
firebase login
firebase use --add
```

## File Structure

```
project/
├── terraform/           # Infrastructure as code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
├── back/                # Backend Python app
├── front/               # Frontend static files
├── secrets/             # Local secrets (gitignored)
│   └── open_api_key.txt
├── docker-compose.yml   # Local development
├── firebase.json        # Firebase configuration
└── .firebaserc         # Firebase project mapping
```

## Security Notes

- Secrets are mounted as files in containers, not environment variables
- All secrets are stored in Google Secret Manager
- Local secrets directory is gitignored
- Terraform state files are gitignored