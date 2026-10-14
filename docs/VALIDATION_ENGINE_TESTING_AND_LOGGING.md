# Validation Engine: Testing & Logging Report

## Hardcore Logging Architecture
The following explicit telemetry nodes must be added to the frontend logger:
*   `[EVENT] VALIDATION_REQUESTED`: Fired when the GT file is selected and sent to `/api/validate`.
*   `[EVENT] VALIDATION_SUCCESS`: Fired when the backend returns RMSE, MAE, and the Heatmap URL. Logs the RMSE value.
*   `[ERROR] VALIDATION_FAILED`: Fired if alignment or CRS matching fails on the backend.
*   `[EVENT] LAYER_SWITCH`: Must be updated to include the `ERROR_HEATMAP` state swap.

## Ruthless Test Cases (Mapped to Faults)

*   **Test Case 1 (Maps to Fault 1 - CRS Mismatch):** 
    *   **Action:** Upload a GT file in a local metric UTM projection.
    *   **Success Condition:** Backend successfully reprojects it to WGS84 and computes the error without crashing.
*   **Test Case 2 (Maps to Fault 2 - Resolution Mismatch):**
    *   **Action:** Upload a GT file with extremely high resolution (e.g., 0.5m/px).
    *   **Success Condition:** The backend resamples it to match our internal array shape perfectly (no `ValueError: operands could not be broadcast together`).
*   **Test Case 3 (Maps to Fault 3 - Bounding Box Offset):**
    *   **Action:** Upload a GT file covering an entire city, while our inference was just on a single block.
    *   **Success Condition:** The backend crops the GT down to our exact bounds before calculation.
*   **Test Case 4 (Maps to Fault 4 - NoData Crashing):**
    *   **Action:** Upload a GT file containing extreme negative values (-9999) for invalid pixels.
    *   **Success Condition:** The RMSE returned is a reasonable number (e.g., 5.4m), not `Infinity` or `NaN`.
*   **Test Case 5 (Maps to Fault 5 - Outlier Skew):**
    *   **Action:** Visual inspection of the Error Heatmap on the 3D terrain.
    *   **Success Condition:** The heatmap has clear red (positive error) and blue (negative error) zones, rather than being a single solid color due to a mathematical outlier.
*   **Test Case 6 (Maps to Fault 6 - Texture Thread Blocking):**
    *   **Action:** Click the "ERROR HEATMAP" layer button rapidly.
    *   **Success Condition:** The browser does not freeze; textures load asynchronously.
