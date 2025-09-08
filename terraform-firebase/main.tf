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

# Enable Firebase on the project
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = data.google_project.project.project_id
  depends_on = [
    google_project_service.apis["firebase.googleapis.com"],
  ]
}

# Create Firebase Hosting site
resource "google_firebase_hosting_site" "default" {
  provider = google-beta
  project  = data.google_project.project.project_id
  site_id  = "meme-analyzer-app"
  depends_on = [
    google_firebase_project.default,
    google_project_service.apis["firebasehosting.googleapis.com"],
  ]
}

# Create Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  provider      = google-beta
  project       = data.google_project.project.project_id
  location      = var.region
  repository_id = "agent-images"
  description   = "Agent Docker images repository (backend and frontend)"
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

# Create secret for Gemini API key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    auto {}
  }

  depends_on = [
    google_project_service.apis["secretmanager.googleapis.com"],
  ]
}

# Grant OpenAI secret access to the service account
resource "google_secret_manager_secret_iam_member" "backend_openai_secret_access" {
  secret_id = google_secret_manager_secret.open_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Grant Gemini secret access to the service account
resource "google_secret_manager_secret_iam_member" "backend_gemini_secret_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Cloud Run service for backend
resource "google_cloud_run_service" "backend" {
  name     = "agent-backend"
  location = var.region
  project  = data.google_project.project.project_id

  template {
    spec {
      service_account_name = google_service_account.backend_sa.email
      containers {
        image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/agent-images/agent-back:latest"
        ports {
          container_port = 8000
        }
        
        # Environment variables matching docker-compose
        env {
          name  = "PYTHONUNBUFFERED"
          value = "1"
        }
        env {
          name  = "LLM_PROVIDER"
          value = "gemini"
        }
        
        # Mount secrets as volumes (matching docker-compose secret paths)
        volume_mounts {
          name       = "secrets-volume"
          mount_path = "/run/secrets"
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      
      # Define the secrets volume with both API keys
      volumes {
        name = "secrets-volume"
        secret {
          secret_name = google_secret_manager_secret.open_api_key.secret_id
          items {
            key  = "latest"
            path = "open_api_key"  # Creates /run/secrets/open_api_key
          }
        }
        secret {
          secret_name = google_secret_manager_secret.gemini_api_key.secret_id
          items {
            key  = "latest"
            path = "gemini_api_key"  # Creates /run/secrets/gemini_api_key
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
    google_artifact_registry_repository.docker_repo,
    google_secret_manager_secret_iam_member.backend_openai_secret_access,
    google_secret_manager_secret_iam_member.backend_gemini_secret_access,
  ]
}

# Cloud Run service for frontend (matching docker-compose architecture)
resource "google_cloud_run_service" "frontend" {
  name     = "agent-frontend"
  location = var.region
  project  = data.google_project.project.project_id

  template {
    spec {
      service_account_name = google_service_account.frontend_sa.email
      containers {
        image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/agent-images/agent-front:latest"
        ports {
          container_port = 3000
        }
        
        # Environment variables matching docker-compose
        env {
          name  = "BACKEND_URL"
          value = google_cloud_run_service.backend.status[0].url
        }
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
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
    google_artifact_registry_repository.docker_repo,
    google_cloud_run_service.backend,
  ]
}

# Allow unauthenticated access to Cloud Run backend service
resource "google_cloud_run_service_iam_member" "backend_public" {
  project  = data.google_project.project.project_id
  location = google_cloud_run_service.backend.location
  service  = google_cloud_run_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to Cloud Run frontend service
resource "google_cloud_run_service_iam_member" "frontend_public" {
  project  = data.google_project.project.project_id
  location = google_cloud_run_service.frontend.location
  service  = google_cloud_run_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service account for Backend Cloud Run
resource "google_service_account" "backend_sa" {
  project      = data.google_project.project.project_id
  account_id   = "agent-backend-sa"
  display_name = "Agent Backend Service Account"

  depends_on = [
    google_project_service.apis["iam.googleapis.com"],
  ]
}

# Service account for Frontend Cloud Run
resource "google_service_account" "frontend_sa" {
  project      = data.google_project.project.project_id
  account_id   = "agent-frontend-sa"
  display_name = "Agent Frontend Service Account"

  depends_on = [
    google_project_service.apis["iam.googleapis.com"],
  ]
}

# Grant necessary permissions to the backend service account
resource "google_project_iam_member" "backend_sa_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor"
  ])

  project = data.google_project.project.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Grant necessary permissions to the frontend service account
resource "google_project_iam_member" "frontend_sa_permissions" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])

  project = data.google_project.project.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.frontend_sa.email}"
}