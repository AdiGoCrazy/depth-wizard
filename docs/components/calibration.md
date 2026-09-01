# Calibration Engine (`src/depth_wizard/calibration.py`)

## Purpose
Converts scale-agnostic relative depth into geographically accurate metric height using low-resolution SRTM DEM anchors and RANSAC linear regression.

## Key Classes & Functions
* `class SRTMCalibrator:`
  * `def fetch_srtm(bounds: dict) -> np.ndarray:` Calls an external open topography API to download the SRTM 30m tile.
  * `def align_and_regress(relative_depth: np.ndarray, srtm_dem: np.ndarray) -> tuple:` Performs RANSAC to find $(s, t)$.
  * `def apply_calibration(relative_depth: np.ndarray, s: float, t: float) -> np.ndarray:` Generates Absolute DSM.

## Inputs & Outputs
* **Input:** `relative_depth` (np.ndarray), `bounds` (dict containing lat/lon box).
* **Output:** `absolute_dsm` (np.ndarray of physical meter values).

## Error Handling
* If `fetch_srtm` times out (10s), raises `CalibrationNetworkError`.
* If RANSAC calculates a physically impossible scale ($s \le 0$), raises `CalibrationFitError`.
