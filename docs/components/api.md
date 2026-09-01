# API Gateway Component (`src/depth_wizard/api.py`)

## Purpose
Acts as the secure, validated entry point for all client requests. Handles HTTP communication, enforces hardware limits on file uploads, and orchestrates the backend modules.

## Key Classes & Functions
* `POST /api/process`: Accepts multipart form-data (image file). Returns a `ProcessImageResponse` JSON.
* `GET /api/status/{job_id}`: (Optional) For async job tracking if processing takes longer than HTTP timeouts.
* `download_asset(filename: str)`: Serves generated GeoTIFFs and meshes.

## Inputs & Outputs
* **Input:** `UploadFile` (multipart form-data). Must be validated via Pydantic/FastAPI constraints (max size 20MB).
* **Output:** JSON response containing `status`, `dsm_url`, `mesh_url`, and `metrics`.

## Error Handling
* Catches and raises HTTP 413 (Payload Too Large) if file exceeds limits.
* Catches HTTP 415 (Unsupported Media Type) if MIME type is not an image.
* Returns HTTP 500 securely (hiding internal stack traces) on pipeline failure, logging the trace internally.
