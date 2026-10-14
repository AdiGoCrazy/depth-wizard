# GeoTIFF Export Feature: Faults & Solutions

As mandated by the methodology, the following is a ruthless critique of the GeoTIFF Export feature. We have identified 6 specific points of failure.

## 1. Fault: Broken Relative URLs in Download Attribute
*   **Severity:** Mild
*   **Description:** The backend returns a relative URL (`/assets/job_id_dsm.tif`). If the frontend attempts to download this via an `<a>` tag with the `download` attribute, the browser might just open the file instead of downloading it if CORS or Content-Disposition headers are missing on the static mount.
*   **Solution (Permanent Architectural Fix):** The frontend JavaScript must dynamically create a Blob via a `fetch()` request and generate an ObjectURL to guarantee a forced download prompt, bypassing generic browser navigation behavior.

## 2. Fault: State Misalignment (Button visible before processing)
*   **Severity:** Mild
*   **Description:** The user clicks the "Download GeoTIFF" button before the image is actually processed, resulting in a 404 or undefined error.
*   **Solution (Permanent Architectural Fix):** Hide the button completely via `display: none` in CSS by default. Only inject the `href` and change it to `display: block` inside the `.then()` block of a successful `/api/process` HTTP response.

## 3. Fault: Missing Metadata Fails TIF Generation
*   **Severity:** Catastrophic
*   **Description:** If the user uploads a basic JPG, it has no geospatial metadata. The backend calibration might fail or return a relative DSM. If the backend still attempts to export a GeoTIFF without a `transform` or `crs`, Rasterio will throw a hard error and crash the endpoint.
*   **Solution (Permanent Architectural Fix):** The backend `export.py` handles missing transforms natively by just writing the array. However, we must ensure the frontend handles the `is_metric` flag. If it's not metric, the exported TIFF is essentially just a relative float array, not a true GeoTIFF. This is acceptable for the problem statement (Relative DSM vs Absolute DSM).

## 4. Fault: Memory Leak from ObjectURLs
*   **Severity:** Moderate
*   **Description:** If we use `URL.createObjectURL(blob)` in JavaScript to force the download, failing to call `URL.revokeObjectURL()` will leave massive 20MB+ binary blobs sitting in the browser's RAM, eventually crashing the page on repeated uploads.
*   **Solution (Permanent Architectural Fix):** Add an explicit `setTimeout(() => URL.revokeObjectURL(url), 5000);` after the `a.click()` event fires in `app.js`.

## 5. Fault: Cross-Origin Resource Sharing (CORS) Block
*   **Severity:** Catastrophic
*   **Description:** If the frontend and backend are run on different ports (e.g., during development), the `fetch()` request to grab the `/assets/` blob will be blocked by CORS policies.
*   **Solution (Preemptive Band-Aid Solution):** Given we are serving the frontend directly from the FastAPI instance (`app.mount("/", ...)`), this won't happen in production. However, we must ensure absolute paths are avoided and relative paths (`/assets/...`) are strictly used.

## 6. Fault: UI Thread Blocking During Blob Conversion
*   **Severity:** Moderate
*   **Description:** Downloading a massive TIFF into a JavaScript Blob and generating an ObjectURL could freeze the UI thread for a few seconds, making the app feel unresponsive.
*   **Solution (Permanent Architectural Fix):** Use an asynchronous `fetch(url).then(res => res.blob())` and display a "Downloading..." loading text on the button while the blob is generated, disabling the button temporarily to prevent spam clicks.
