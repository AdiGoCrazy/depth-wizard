# Test-Driven Preparation Plan (`tests/`)

Comprehensive test cases mapped directly to the edge cases identified in Phase 1 and Phase 2.

## 1. Ingestion Tests (`test_ingestion.py`)
* **Test:** Upload valid GeoTIFF. **Expected:** Returns RGB array + valid CRS metadata.
* **Test:** Upload non-georeferenced PNG. **Expected:** Returns RGB array + `metadata=None`.
* **Test:** Upload massive 4K GeoTIFF. **Expected:** `_validate_dimensions()` triggers and downsamples to max 2048x2048.
* **Test:** Upload corrupt/text file spoofed as `.tif`. **Expected:** Throws `IngestionError` or `ValueError`.

## 2. MDE Engine Tests (`test_model.py`)
* **Test:** Predict on valid 1024x1024 array. **Expected:** Outputs 1024x1024 relative depth map bounded [0, 1].
* **Test:** Shadow Pre-processor. **Expected:** Input array with deep black shadows should output an array with those shadows lightened.
* **Test:** Guided Filter. **Expected:** Output depth map edges align closer to original RGB edges than the raw depth map.

## 3. Calibration Engine Tests (`test_calibration.py`)
* **Test:** RANSAC fitting on valid synthetic mock data. **Expected:** Calculates $s$ and $t$ within 5% tolerance of expected values.
* **Test:** Impossible RANSAC fit. **Expected:** Throws `CalibrationFitError` if scale $s$ is negative.
* **Test:** Network Timeout Mock. **Expected:** `fetch_srtm` raises `CalibrationNetworkError` when the mocked request times out.

## 4. API Gateway End-to-End Tests (`test_api.py`)
* **Test:** Valid end-to-end relative flow (PNG upload). **Expected:** HTTP 200, returns JSON with `is_metric=False` and valid asset URLs.
* **Test:** Invalid file size. **Expected:** HTTP 413 Payload Too Large.
* **Test:** Environment `urban`. **Expected:** Triggers full pipeline (Preprocessor + FastSAM).
* **Test:** Environment `terrain`. **Expected:** Bypasses Preprocessor and FastSAM completely.
* **Test:** Invalid Environment Payload. **Expected:** HTTP 422 or graceful fallback to `urban` (HTTP 200).

## 5. Segmentation Engine Tests (`test_segmentation.py`)
* **Test:** VRAM Swap Protocol. **Expected:** Loading to GPU spikes VRAM, unloading completely clears the allocated VRAM back to the original baseline without memory leaks.
* **Test:** Generate Masks Valid Output. **Expected:** Engine successfully executes the SAM generator and returns a list of binary masks that match the input dimensions.

## 6. Preprocessing Engine Tests (`test_preprocessing.py`)
* **Test:** CLAHE Validation. **Expected:** Image is modified in L-channel without altering dimensions or dtype.
* **Test:** Shadow Enhancement. **Expected:** The mean pixel value of pre-existing dark regions strictly decreases.
* **Test:** Invalid Dtype Handling. **Expected:** Throws `ValueError` or `TypeError` if fed float arrays instead of `uint8`.
