# DepthWizard Backend Architecture (Phase 1)

This document represents the Phase 1 Initial Planning & Architecture for the DepthWizard backend, strictly adhering to the `develop` skill structured engineering principles.

---

## 1. Requirement Analysis & Stack Adaptation
**Objective:** Develop a robust, modular, and scalable Python backend to handle ingestion, monocular depth inference, scale calibration, and GeoTIFF export.
**Ecosystem:** 
* **Package Manager:** `uv` (Python 3.13)
* **API Framework:** `FastAPI` (with `Uvicorn`)
* **ML Framework:** `PyTorch` (targeting `Depth Anything V2` backbone)
* **Geospatial Processing:** `rasterio`, `geopandas`
* **Math & Calibration:** `numpy`, `scikit-learn` (RANSAC)

---

## 2. Resource & Hardware Profiling
To prevent catastrophic out-of-memory (OOM) failures during remote sensing inference, we establish the following hardware constraints:
* **VRAM Constraint:** Hard cap at **4GB VRAM** target. We will utilize the `Depth Anything V2 Small` checkpoint by default, which consumes ~1.5GB during 1024x1024 inference.
* **System RAM:** 8GB minimum target. Large GeoTIFF arrays can spike memory. We will strictly enforce maximum processing dimensions.
* **Processing Caps:** Input image resolutions exceeding `2048 x 2048` pixels will be rejected at the API gateway or automatically downsampled to prevent memory overflow.

---

## 3. Visual & Structural Mapping

### Backend Execution Flowchart
```mermaid
graph TD
    A[Client Request: POST /api/process] --> B(API Gateway / Validator)
    
    B -->|Invalid| C[Return 400 Bad Request]
    B -->|Valid Image| D[Ingestion Module]
    
    D --> E{Has Geo-Metadata?}
    E -->|No| F[Process as Relative Image]
    E -->|Yes: Extracts CRS, Bounds| G[Process as Georeferenced]
    
    %% ML Pipeline
    F --> H[Shadow Pre-processor]
    G --> H
    H --> I[PyTorch MDE Engine]
    I --> J[Relative Depth Map (0-1)]
    J --> K[Guided Filter Edge Alignment]
    
    %% Calibration Pipeline
    K -.->|If Georeferenced| L[Calibration Engine]
    G -.->|Pass Bounds| L
    L -->|Fetch SRTM API| M[(SRTM 30m DEM)]
    M --> L
    L -->|RANSAC Regression Z=sZ+t| N[Absolute Metric DSM]
    
    %% Export
    K -.->|If Relative| O[Export relative PNG/Mesh]
    N --> P[Export GeoTIFF]
    
    O --> Q[Return HTTP 200: Assets URL]
    P --> Q
```

### Strict Data Models (JSON Schemas)

**Input: Process Image Request (Form-Data / Multipart)**
```json
{
  "title": "ProcessImageRequest",
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "The image file (GeoTIFF, PNG, JPG). Max size 20MB."
    },
    "mode": {
      "type": "string",
      "enum": ["auto", "georeferenced", "relative"],
      "default": "auto"
    }
  },
  "required": ["file"]
}
```

**Output: Process Image Response**
```json
{
  "title": "ProcessImageResponse",
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["success", "error"] },
    "is_metric": { "type": "boolean", "description": "True if SRTM calibration succeeded" },
    "dsm_url": { "type": "string", "description": "Download link for GeoTIFF DSM" },
    "mesh_url": { "type": "string", "description": "Download link for 3D displacement map" },
    "metrics": {
      "type": "object",
      "properties": {
        "rmse": { "type": "number", "nullable": true },
        "calibration_scale": { "type": "number", "nullable": true },
        "calibration_shift": { "type": "number", "nullable": true }
      }
    }
  },
  "required": ["status", "is_metric", "dsm_url"]
}
```

---

## 4. Threat & Failure Modeling (Unintended Consequences Report)

| Threat / Risk | Consequence | Mitigation Strategy |
| :--- | :--- | :--- |
| **CUDA OOM Error** | Server crashes during inference of a massive (e.g., 4K+) GeoTIFF. | Enforce strict `2048x2048` dimension limits at the FastAPI gateway. Downsample before tensor conversion. |
| **SRTM API Timeout** | Process hangs waiting for OpenTopography/SRTM download, leaving API connection dangling. | Implement strict 10-second timeout on HTTP requests. Fall back to relative depth mode if unreachable. |
| **Invalid/Missing CRS in TIFF** | `rasterio` throws exception during reprojection or bounds calculation. | Wrap ingestion in robust `try-except` blocks. If CRS is missing or invalid, flag `is_metric = False` and process as a standard PNG. |
| **Adversarial / Malformed File** | Directory traversal attack or code execution via malicious `.tiff` headers. | Use secure file staging (temp UUID directories), sanitize filenames, and strictly validate MIME types using `python-magic` before `rasterio` opens it. |
| **Corrupt SRTM Calibration** | RANSAC fits a wild scale factor ($s < 0$), resulting in inverted/broken terrain. | Enforce physical constraints on scale factor $s > 0$ and realistic bounds. Reject calibration and return relative depth if constraints fail. |

---

## 5. User Gate
Phase 1 complete. Awaiting user approval to proceed to **Phase 2 (Modular Documentation & Test Planning)**.
