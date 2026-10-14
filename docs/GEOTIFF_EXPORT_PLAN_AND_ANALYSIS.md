# GeoTIFF Export Feature: Plan & Analysis

## Overview
The goal of this feature is to allow users to download the mathematically absolute Digital Surface Model (DSM) calculated by the backend in a standard, geospatial industry format (GeoTIFF, `.tif`). 

## Backend Analysis
Upon investigating the Python backend (`src/depth_wizard/api.py` and `export.py`), the heavy lifting is already implemented. The `Exporter` class successfully writes the GeoTIFF via `rasterio` using LZW compression and returns a `dsm_url` within the JSON payload of the `/api/process` endpoint.

## Proposed Frontend Implementation
The development will strictly focus on the frontend (`index.html` and `app.js`).
1.  **UI Addition:** Inject a "DOWNLOAD DSM (.TIF)" button into the `actions` div alongside the "UPLOAD SATELLITE IMAGE" button.
2.  **State Management:** The button must remain `disabled` or hidden until a successful response is received from `/api/process`.
3.  **Action Binding:** Upon success, the `dsm_url` from the JSON response will be bound to the button. Clicking the button will trigger an HTML5 download anchor, securely pulling the asset from the `/assets/` static mount.

## Advantages
*   **Zero Backend Cost:** No new Python dependencies (`rasterio`, `gdal`) are required since it is already integrated.
*   **Industry Standard:** Fulfills the SIH requirement to output geospatial data, bridging our app to QGIS/ArcGIS.

## Disadvantages
*   **Large File Transfers:** GeoTIFFs can be massive (20MB+). Downloading them over unstable networks could cause timeouts.
*   **Browser Security:** Browsers heavily restrict automatic downloads or blob generation. We must ensure the download is triggered by a direct user interaction event to avoid popup blockers.
