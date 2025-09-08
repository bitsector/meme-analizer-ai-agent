variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "gcp-cloud-run-tests"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, start with a letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "project_name" {
  description = "The display name for the GCP project"
  type        = string
  default     = "Agent Dolph Firebase Project"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "org_id" {
  description = "The GCP organization ID (optional, leave empty if using personal account)"
  type        = string
  default     = null
}

variable "billing_account" {
  description = "The GCP billing account ID (format: XXXXXX-XXXXXX-XXXXXX or full billing account name)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}