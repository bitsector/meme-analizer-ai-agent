output "project_id" {
  description = "The GCP project ID"
  value       = data.google_project.project.project_id
}

output "project_number" {
  description = "The GCP project number"
  value       = data.google_project.project.number
}

# Firebase outputs commented out due to permission issues
# output "firebase_project_id" {
#   description = "The Firebase project ID"
#   value       = google_firebase_project.default.project
# }

# output "firebase_hosting_site_id" {
#   description = "The Firebase Hosting site ID"
#   value       = google_firebase_hosting_site.default.site_id
# }

output "cloud_run_backend_url" {
  description = "The Cloud Run backend service URL"
  value       = google_cloud_run_service.backend.status[0].url
}

output "artifact_registry_repository" {
  description = "The Artifact Registry repository for backend images"
  value       = google_artifact_registry_repository.backend_repo.name
}

output "backend_image_url" {
  description = "The full backend Docker image URL"
  value       = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/backend-images/agent-back"
}

output "functions_service_account_email" {
  description = "The Firebase Functions service account email"
  value       = google_service_account.functions_sa.email
}

output "region" {
  description = "The GCP region used for resources"
  value       = var.region
}