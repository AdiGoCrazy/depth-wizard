# Validation Engine: Faults & Solutions

As mandated by our engineering methodology, this is a ruthless critique of the Automated Validation Engine implementation.

## 1. Fault: Coordinate Reference System (CRS) Mismatch
*   **Severity:** Catastrophic
*   **Description:** The Ground Truth `.tif` (e.g., LiDAR) might be projected in a local UTM CRS (e.g., EPSG:32643), while our generated DSM is exported in WGS84 (EPSG:4326). Direct matrix subtraction will fail entirely.
*   **Solution (Permanent Architectural Fix):** The backend must use `rasterio.warp.reproject` to force the GT dataset into the exact CRS of our generated DSM before any mathematical operations occur.

## 2. Fault: Spatial Resolution (Grid Size) Misalignment
*   **Severity:** Catastrophic
*   **Description:** The GT data might be 1m resolution (1000x1000 pixels), while our generated DSM is 2m resolution (500x500 pixels). Arrays of different shapes cannot be subtracted.
*   **Solution (Permanent Architectural Fix):** During the reprojection phase, we must mathematically resample (using Bilinear interpolation) the GT array to perfectly match the `(width, height)` shape of our generated DSM.

## 3. Fault: Bounding Box Offset (Extents Mismatch)
*   **Severity:** Moderate
*   **Description:** The user might upload a massive regional GT LiDAR file that covers a much larger area than our specific inference window.
*   **Solution (Permanent Architectural Fix):** The backend must read the spatial `bounds` (left, bottom, right, top) of our generated DSM and crop the GT dataset using a spatial mask before resampling it.

## 4. Fault: NoData / NaN Values Crashing Numpy
*   **Severity:** Catastrophic
*   **Description:** LiDAR datasets frequently contain `-9999` or `NaN` values over water or invalid sensors points. Subtracting this will result in an RMSE of infinity.
*   **Solution (Permanent Architectural Fix):** We must create a boolean mask (`valid_mask = (gt_array != nodata) & ~np.isnan(gt_array)`) and only calculate RMSE/MAE and heatmap colors on valid overlapping pixels.

## 5. Fault: Outliers Skewing the Color Heatmap
*   **Severity:** Mild
*   **Description:** A single extreme outlier pixel (e.g., error of +1000m due to a glitch) will compress the entire color ramp of the heatmap, making the rest of the map look perfectly fine (neutral) because the max value is so high.
*   **Solution (Preemptive Band-Aid Solution):** When generating the heatmap texture via OpenCV/Matplotlib, we will clip the error values to the 5th and 95th percentiles (vMin/vMax) before applying the color map, ensuring high-contrast visual feedback.

## 6. Fault: UI Thread Freezing during Heatmap Texture Swap
*   **Severity:** Mild
*   **Description:** When the user clicks the "ERROR HEATMAP" layer button, loading a high-res JPG texture synchronously into Three.js might drop frames.
*   **Solution (Permanent Architectural Fix):** Ensure `THREE.TextureLoader().load()` is used with its asynchronous callback, and log the texture load latency via the `logger.js` telemetry system.
