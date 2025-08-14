terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Use existing GCP project
data "google_project" "project" {
  project_id = var.project_id
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  project = data.google_project.project.project_id
  service = each.value

  disable_dependent_services = true
  disable_on_destroy         = false
}

# Firebase resources commented out due to permission issues
# Uncomment and run again once Firebase Admin role is properly configured

# resource "google_firebase_project" "default" {
#   provider = google-beta
#   project  = data.google_project.project.project_id
#   depends_on = [
#     google_project_service.apis["firebase.googleapis.com"],
#   ]
# }

# resource "google_firebase_hosting_site" "default" {
#   provider = google-beta
#   project  = data.google_project.project.project_id
#   site_id  = var.project_id
# }

# Create Artifact Registry for Docker images
resource "google_artifact_registry_repository" "backend_repo" {
  provider      = google-beta
  project       = data.google_project.project.project_id
  location      = var.region
  repository_id = "backend-images"
  description   = "Backend Docker images repository"
  format        = "DOCKER"

  depends_on = [
    google_project_service.apis["artifactregistry.googleapis.com"],
  ]
}

# Create secret for OpenAI API key
resource "google_secret_manager_secret" "open_api_key" {
  secret_id = "open-api-key"
  
  replication {
    auto {}
  }

  depends_on = [
    google_project_service.apis["secretmanager.googleapis.com"],
  ]
}

# Grant secret access to the service account
resource "google_secret_manager_secret_iam_member" "backend_secret_access" {
  secret_id = google_secret_manager_secret.open_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.functions_sa.email}"
}

# Cloud Run service for backend
resource "google_cloud_run_service" "backend" {
  name     = "agent-backend"
  location = var.region
  project  = data.google_project.project.project_id

  template {
    spec {
      service_account_name = google_service_account.functions_sa.email
      containers {
        image = "gcr.io/cloudrun/hello"
        ports {
          container_port = 8000
        }
        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
        
        # Mount secret as volume
        volume_mounts {
          name       = "openai-secret-volume"
          mount_path = "/run/secrets"
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      
      # Define the secret volume
      volumes {
        name = "openai-secret-volume"
        secret {
          secret_name = google_secret_manager_secret.open_api_key.secret_id
          items {
            key  = "latest"
            path = "open_api_key"  # Creates /run/secrets/open_api_key
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.apis["run.googleapis.com"],
    google_artifact_registry_repository.backend_repo,
    google_secret_manager_secret_iam_member.backend_secret_access,
  ]
}

# Allow unauthenticated access to Cloud Run service
resource "google_cloud_run_service_iam_member" "backend_public" {
  project  = data.google_project.project.project_id
  location = google_cloud_run_service.backend.location
  service  = google_cloud_run_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service account for Firebase Functions
resource "google_service_account" "functions_sa" {
  project      = data.google_project.project.project_id
  account_id   = "firebase-functions-sa"
  display_name = "Firebase Functions Service Account"

  depends_on = [
    google_project_service.apis["iam.googleapis.com"],
  ]
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "functions_sa_permissions" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor"
  ])

  project = data.google_project.project.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}