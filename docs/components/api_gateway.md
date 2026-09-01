# API Gateway Component

**Path:** `src/depth_wizard/api.py`

## Purpose
The API Gateway serves as the single orchestration layer for the DepthWizard backend. It receives the multipart form data from the frontend, manages the sequential lifecycle of the AI models (to respect the VRAM limits), and handles the final geometric export.

## Core Responsibilities (Updated)
-   **Environment Context Forking:** Extracts the `environment` string from the payload (`"urban"` or `"terrain"`). 
    -   If `"urban"`, the pipeline executes the full suite: `ImagePreprocessor -> DepthModel -> SegmentationEngine -> Mask Flattening`.
    -   If `"terrain"`, the pipeline executes the minimal suite: `DepthModel`. The preprocessor and segmentation engines are entirely bypassed.
-   **VRAM Orchestration:** Explicitly calls `.load_to_gpu()` and `.unload_to_cpu()` on the heavy AI models to ensure `Depth Anything V2` and `FastSAM` never reside in GPU memory simultaneously.

## Security & Data Integrity
-   **Parameter Validation:** The `environment` parameter defaults to `"urban"`. If an unrecognized string is sent (e.g., `"city"`), it is coerced to `"urban"` or raises a strict validation error depending on implementation.
-   **Payload Size Limits:** Enforces a strict 20MB limit to prevent Denial of Service via massive GeoTIFF uploads.

## Logging Strategy
-   `INFO`: Report which environment execution branch was chosen.
-   `WARNING`: Report if an invalid environment string was passed and fallback occurred.
