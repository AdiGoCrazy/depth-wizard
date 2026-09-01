# Ingestion Module (`src/depth_wizard/ingestion.py`)

## Purpose
Securely loads image data into memory, sanitizes it, and extracts spatial metadata (CRS, GeoTransform, Bounding Box) for geospatial routing.

## Key Classes & Functions
* `class ImageIngestor:`
  * `def load_image(filepath: Path) -> np.ndarray:` Reads image into RGB numpy array.
  * `def extract_metadata(filepath: Path) -> dict:` Uses `rasterio` to fetch EPSG code and bounds.
  * `def _validate_dimensions(image: np.ndarray) -> np.ndarray:` Enforces the 2048x2048 hard cap. Downsamples using `cv2` if necessary.

## Inputs & Outputs
* **Input:** Validated local filepath to the staged upload.
* **Output:** `(rgb_array: np.ndarray, metadata: Optional[dict])`

## Error Handling
* Raises `IngestionError` if `rasterio` or `PIL` fails to open the file (corrupt file).
* Warns (does not fail) if CRS is missing, simply returning `metadata = None` (triggering fallback relative mode).
