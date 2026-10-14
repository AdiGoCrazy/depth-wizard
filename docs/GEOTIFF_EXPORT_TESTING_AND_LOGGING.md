# GeoTIFF Export Feature: Testing & Logging Report

## Hardcore Logging Architecture
The UI currently has a realtime logger HUD (controlled via `logger.js`). The new export feature must hook into this architecture explicitly:
*   `[EVENT] GEOTIFF_EXPORT_INITIATED`: Logged the moment the user clicks the download button.
*   `[EVENT] GEOTIFF_BLOB_GENERATED`: Logged when the fetch completes and the binary blob is created in RAM (include blob size in MB).
*   `[EVENT] GEOTIFF_EXPORT_SUCCESS`: Logged immediately before `URL.revokeObjectURL()` fires, confirming the download action completed.
*   `[ERROR] GEOTIFF_EXPORT_FAILED`: Logged if the fetch promise rejects.

## Ruthless Test Cases (Mapped to Faults)

*   **Test Case 1 (Maps to Fault 1 - Broken URLs):** 
    *   **Action:** Click Download.
    *   **Success Condition:** The browser natively downloads a `.tif` file to the local disk, rather than navigating away or opening the file in a new tab as garbage text.
*   **Test Case 2 (Maps to Fault 2 - State Misalignment):**
    *   **Action:** Reload the application. Do not upload an image.
    *   **Success Condition:** The "DOWNLOAD DSM" button is completely invisible/unclickable.
*   **Test Case 3 (Maps to Fault 3 - Missing Metadata):**
    *   **Action:** Upload a standard `.jpg` (no geospatial metadata). Click download.
    *   **Success Condition:** The system still successfully downloads a `.tif` file (a relative DSM) without crashing the backend or throwing 500 Server Errors.
*   **Test Case 4 (Maps to Fault 4 - Memory Leak):**
    *   **Action:** Upload an image and click download 5 times in a row. Monitor browser memory.
    *   **Success Condition:** Memory usage does not monotonically increase by 20MB per click; `revokeObjectURL` clears the cache correctly.
*   **Test Case 5 (Maps to Fault 5 - CORS Block):**
    *   **Action:** Verify the network tab during the blob fetch.
    *   **Success Condition:** The `fetch()` request is strictly relative to the root domain (`/assets/`) and does not throw a cross-origin error.
*   **Test Case 6 (Maps to Fault 6 - UI Thread Blocking):**
    *   **Action:** Click the download button on a massive GeoTIFF. 
    *   **Success Condition:** The button text immediately changes to "Downloading..." and becomes disabled, providing visual feedback before the blob conversion completes.

The project is considered incomplete if ANY of these test cases fail.
