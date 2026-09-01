# State, Memory, and Security Architecture

## State & Memory Architecture
The DepthWizard backend is designed to be **stateless and ephemeral**.
* **Memory Lifecycle:** Uploaded GeoTIFFs are temporarily loaded into RAM during the lifetime of a single API request. Once inference and export are complete, all intermediate numpy arrays and PyTorch tensors are explicitly deleted, and `torch.cuda.empty_cache()` is called to prevent memory fragmentation.
* **Persistent Storage:** The final generated assets (GeoTIFF DSM, mesh files) are saved to a temporary local disk directory (`/tmp/depthwizard_exports/` or a configurable mounted volume) with a unique UUID. These files are served via static file routing. A cron job or background task should purge files older than 24 hours.

## Security & Secrets Mapping
* **Secrets Handling:** The API will require `.env` integration. 
  * `SRTM_API_KEY`: If an external API (like OpenTopography) requires authentication to fetch the DEM anchor, it must be loaded via `python-dotenv` and never hardcoded.
* **Input Validation:**
  * Pydantic models will validate all incoming requests.
  * File uploads will be checked using `python-magic` to ensure the MIME type is an actual image, mitigating malicious file uploads.
  * File sizes are capped at 20MB.
