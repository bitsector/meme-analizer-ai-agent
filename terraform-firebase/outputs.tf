output "project_id" {
  description = "The GCP project ID"
  value       = data.google_project.project.project_id
}

output "project_number" {
  description = "The GCP project number"
  value       = data.google_project.project.number
}

output "firebase_project_id" {
  description = "The Firebase project ID"
  value       = google_firebase_project.default.project
}

output "firebase_hosting_site_id" {
  description = "The Firebase Hosting site ID"
  value       = google_firebase_hosting_site.default.site_id
}

output "cloud_run_backend_url" {
  description = "The Cloud Run backend service URL"
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_run_frontend_url" {
  description = "The Cloud Run frontend service URL"
  value       = google_cloud_run_service.frontend.status[0].url
}

output "artifact_registry_repository" {
  description = "The Artifact Registry repository for Docker images"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "backend_image_url" {
  description = "The full backend Docker image URL"
  value       = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/agent-images/agent-back"
}

output "frontend_image_url" {
  description = "The full frontend Docker image URL"
  value       = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/agent-images/agent-front"
}

output "backend_service_account_email" {
  description = "The Backend service account email"
  value       = google_service_account.backend_sa.email
}

output "frontend_service_account_email" {
  description = "The Frontend service account email"
  value       = google_service_account.frontend_sa.email
}

output "region" {
  description = "The GCP region used for resources"
  value       = var.region
}