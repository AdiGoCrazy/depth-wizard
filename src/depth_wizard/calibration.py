import logging
import numpy as np
from sklearn.linear_model import RANSACRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from typing import Tuple, Dict

logger = logging.getLogger("depth_wizard.calibration")

class CalibrationNetworkError(Exception):
    pass

class CalibrationFitError(Exception):
    pass

class SRTMCalibrator:
    @staticmethod
    def fetch_srtm(bounds: Dict[str, float], target_shape: Tuple[int, int]) -> np.ndarray:
        """
        Mocks fetching SRTM 30m DEM for the given bounding box.
        In production, this would make an HTTP request to OpenTopography API.
        """
        logger.info(f"[Calibration] Fetching SRTM DEM for bounds: {bounds}")
        # Mock API delay and data generation
        # Real SRTM might range from 0 to 8000m. Let's mock a terrain of 100m to 300m height.
        h, w = target_shape
        mock_dem = np.random.uniform(100.0, 300.0, size=(h, w)).astype(np.float32)
        
        # Add spatial gradient to simulate a slope
        gradient_x = np.linspace(0, 50, w)
        gradient_y = np.linspace(0, 50, h)
        xv, yv = np.meshgrid(gradient_x, gradient_y)
        mock_dem += xv + yv
        
        logger.debug("[Calibration] SRTM DEM fetch complete.")
        return mock_dem

    @classmethod
    def align_and_regress(cls, relative_depth: np.ndarray, srtm_dem: np.ndarray) -> Tuple[float, float, dict]:
        """
        Fits Z_metric = s * Z_rel + t using RANSAC.
        Returns scale (s), shift (t), and metrics.
        """
        logger.info("[Calibration] Running RANSAC robust linear regression.")
        
        # Flatten arrays for regression
        X = relative_depth.flatten().reshape(-1, 1)
        y = srtm_dem.flatten()
        
        # Randomly sample pixels to speed up regression on large images
        sample_size = min(len(y), 10000)
        idx = np.random.choice(np.arange(len(y)), sample_size, replace=False)
        X_sample = X[idx]
        y_sample = y[idx]
        
        ransac = RANSACRegressor(random_state=42)
        try:
            ransac.fit(X_sample, y_sample)
        except ValueError as e:
            raise CalibrationFitError(f"RANSAC failed to fit: {e}")
            
        scale = float(ransac.estimator_.coef_[0])
        shift = float(ransac.estimator_.intercept_)
        
        if scale <= 0:
            logger.error(f"[Calibration] Invalid scale {scale}. RANSAC fit inverted.")
            raise CalibrationFitError("Calculated scale is negative or zero. Fit failed physical constraints.")
            
        logger.info(f"[Calibration] Fit success: Z = {scale:.2f} * Z_rel + {shift:.2f}")
        
        # Calculate metrics against the anchor DEM
        y_pred = ransac.predict(X_sample)
        rmse = float(np.sqrt(mean_squared_error(y_sample, y_pred)))
        mae = float(mean_absolute_error(y_sample, y_pred))
        
        metrics = {
            "rmse": rmse,
            "mae": mae,
            "r2_score": float(ransac.score(X_sample, y_sample))
        }
        return scale, shift, metrics

    @staticmethod
    def apply_calibration(relative_depth: np.ndarray, scale: float, shift: float) -> np.ndarray:
        logger.debug("[Calibration] Applying absolute metric transformation.")
        absolute_dsm = (relative_depth * scale) + shift
        return absolute_dsm.astype(np.float32)
