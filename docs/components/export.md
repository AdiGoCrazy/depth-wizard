# Export Module (`src/depth_wizard/export.py`)

## Purpose
Packages the output NumPy arrays into standardized formats for the frontend and geospatial end-users.

## Key Classes & Functions
* `class Exporter:`
  * `def export_geotiff(dsm: np.ndarray, metadata: dict, output_path: Path):` Writes the metric array to a TIFF with CRS tags using `rasterio`.
  * `def export_3d_mesh_data(dsm: np.ndarray, rgb: np.ndarray, output_path: Path):` Quantizes and exports the heightmap for Three.js consumption.

## Inputs & Outputs
* **Input:** `dsm` (np.ndarray), `metadata` (dict).
* **Output:** Returns File paths (`Path`) to the saved assets on disk.

## Error Handling
* Raises `IOError` if disk is full or directory permissions block writing.
