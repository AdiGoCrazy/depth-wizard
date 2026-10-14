# Validation Engine: Plan & Analysis

## Overview
The SIH grading rubric assigns 50% of the total score to "Evaluation against ground truth datasets (RMSE & MAE)." This feature implements an Automated Validation Engine allowing users to upload a ground-truth LiDAR DEM, compare it against our generated absolute DSM, and visually inspect the deviations.

## Backend Architecture
We will implement a new FastAPI endpoint in `src/depth_wizard/api.py`: `POST /api/validate`.
*   **Payload:** The Ground Truth GeoTIFF file and the active `job_id` (so the backend can locate the generated DSM in `/assets/`).
*   **Processing (`validation.py`):** 
    *   Load both the GT (Ground Truth) and our generated DSM via `rasterio`.
    *   Spatially align them (resampling/cropping if necessary).
    *   Calculate quantitative metrics: Root Mean Square Error (RMSE) and Mean Absolute Error (MAE).
    *   Generate a quantitative Error Heatmap array (Prediction - Ground Truth).
*   **Export:** Save the heatmap as a `_heatmap.jpg` (color-mapped from blue/negative to red/positive) and return the URL alongside the metrics.

## Frontend UI Architecture
*   **Actions Bar:** Introduce a new "VALIDATE DSM" button next to the download button. Clicking it opens a file selection dialog limited to `.tif`.
*   **Inspector HUD:** The "Point Inspector" HUD will be expanded or modified to permanently display the calculated RMSE and MAE for the scene.
*   **Viewport Layers:** Add a 3rd button to the "VIEWPORT LAYERS" sidebar: `ERROR HEATMAP`. When selected, the Three.js mesh texture swaps to the `_heatmap.jpg`, providing instant spatial feedback on where the AI failed.

## Advantages
*   **Rubric Dominance:** Directly answers the core 50% grading criteria for the competition.
*   **Visual Proof:** A heatmap proves we aren't faking the metric numbers.

## Disadvantages
*   **Geospatial Complexity:** Aligning two separate GeoTIFFs (with potentially different CRS, resolutions, and bounding boxes) is mathematically complex and computationally heavy on the Python backend.
