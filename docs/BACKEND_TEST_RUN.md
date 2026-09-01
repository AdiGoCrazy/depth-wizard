# Backend Integration Test Run

This document outlines the expected behavior when running a live integration test against the DepthWizard backend. As the test runs, the expected processes will be verified and checked off.

## 1. Test Input
* **Image Type:** Synthetic non-georeferenced `.jpg` (512x512 pixels). We will generate this on the fly to simulate a standard RGB upload.
* **API Endpoint:** `POST /api/process` via FastAPI `TestClient`.

## 2. Expected Processes (Pipeline Flow)
- [x] **API Gateway:** Receives multipart form-data upload and stages it securely.
- [x] **Ingestion Module:** Loads the 512x512 image into a normalized NumPy array and correctly identifies that spatial metadata is missing (falling back to relative mode).
- [x] **MDE Engine (Initialization):** PyTorch Hub downloads and caches the `Depth Anything V2` weights (only happens on the first run).
- [x] **MDE Engine (Pre-processing):** Executes the HSV shadow mitigation logic.
- [x] **MDE Engine (Inference):** Executes the true Depth Anything neural network inference inside `torch.no_grad()`.
- [x] **MDE Engine (Post-processing):** Applies the bilateral/guided filter for edge snapping.
- [x] **Calibration Engine:** Bypasses SRTM fetch and RANSAC since `is_metric` defaults to False for standard JPGs.
- [x] **Export Module:** Serializes the relative depth array into a local `.tif` and a mesh `.json` inside `/tmp/depthwizard_exports`.

## 3. Expected Output
- **HTTP Status:** 200 OK
- **JSON Response Payload:**
  ```json
  {
    "status": "success",
    "is_metric": false,
    "dsm_url": "/assets/<uuid>_dsm.tif",
    "mesh_url": "/assets/<uuid>_mesh.json",
    "metrics": null
  }
  ```
- **File Verification:** The `.tif` and `.json` files must physically exist on disk in the asset storage directory.
