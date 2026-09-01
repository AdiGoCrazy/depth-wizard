# Structured Logging Architecture

The backend will implement a scalable, leveled logging strategy to trace API requests, inference profiling, and errors without creating a monolithic log file.

## Log Levels
* **DEBUG:** Used for detailed VRAM profiling (e.g., memory before/after inference), RANSAC iteration tracking, and network timing for SRTM fetches.
* **INFO:** Core state changes (e.g., "Received 1024x1024 GeoTIFF", "Inference complete in 1.2s", "Exported UUID-xyz.tif").
* **WARN:** Non-fatal recoveries (e.g., "No CRS found in GeoTIFF, falling back to relative mode", "CUDA OOM caught, falling back to CPU").
* **ERROR:** Fatal API request failures (e.g., "SRTM API Timeout", "Invalid File Upload"). Includes sanitized stack traces.

## Component Categorization
Logs will be categorized by module for easy grep filtering:
* `[API Gateway]`
* `[Ingestion]`
* `[MDE Engine]`
* `[Calibration]`
* `[Export]`
