import logging
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds
import cv2
from pathlib import Path

logger = logging.getLogger("depth_wizard.validation")

class ValidationEngine:
    @staticmethod
    def calculate_metrics_and_heatmap(predicted_dsm_path: str, gt_dsm_path: str, output_heatmap_path: str):
        """
        Calculates RMSE and MAE between predicted and ground truth GeoTIFFs,
        and generates a visual error heatmap.
        """
        try:
            with rasterio.open(predicted_dsm_path) as src_pred:
                pred_dsm = src_pred.read(1)
                pred_meta = src_pred.meta
                pred_bounds = src_pred.bounds
                pred_crs = src_pred.crs

            with rasterio.open(gt_dsm_path) as src_gt:
                gt_crs = src_gt.crs
                
                # Fault 3 Solution: Crop GT to Pred Bounds if GT is larger, or just rely on reproject.
                # Reproject handles both CRS mismatch (Fault 1) and Resolution mismatch (Fault 2).
                
                logger.info(f"[Validation Engine] Reprojecting Ground Truth to match Predicted CRS/Resolution...")
                
                # Destination array for resampled GT
                aligned_gt = np.zeros_like(pred_dsm)
                
                reproject(
                    source=rasterio.band(src_gt, 1),
                    destination=aligned_gt,
                    src_transform=src_gt.transform,
                    src_crs=gt_crs,
                    dst_transform=pred_meta['transform'],
                    dst_crs=pred_crs,
                    resampling=Resampling.bilinear
                )
                
                nodata = src_gt.nodata if src_gt.nodata is not None else -9999.0
                
                # Fault 4 Solution: NoData/NaN Masking
                valid_mask = (aligned_gt != nodata) & (~np.isnan(aligned_gt)) & (aligned_gt != 0.0) & (~np.isnan(pred_dsm))
                
                if not np.any(valid_mask):
                    raise ValueError("No valid overlapping pixels between GT and Prediction.")
                
                gt_valid = aligned_gt[valid_mask]
                pred_valid = pred_dsm[valid_mask]
                
                error_array = pred_valid - gt_valid
                
                rmse = np.sqrt(np.mean(error_array ** 2))
                mae = np.mean(np.abs(error_array))
                
                logger.info(f"[Validation Engine] Validation Complete: RMSE={rmse:.2f}m, MAE={mae:.2f}m")
                
                # Heatmap Generation
                # We need to map the error back to the full 2D spatial array
                spatial_error = np.zeros_like(pred_dsm, dtype=np.float32)
                spatial_error[valid_mask] = error_array
                
                # Fault 5 Solution: Outlier Skew Rejection for Visualization
                if len(error_array) > 0:
                    vmin = np.percentile(error_array, 5)
                    vmax = np.percentile(error_array, 95)
                else:
                    vmin, vmax = -10, 10
                    
                logger.info(f"[Validation Engine] Heatmap clamping range: [{vmin:.2f}, {vmax:.2f}]")
                
                # Normalize error to 0-255 based on vmin/vmax
                # Center around 0
                abs_max = max(abs(vmin), abs(vmax), 1e-5)
                
                # Map -abs_max to 0, 0 to 127, abs_max to 255
                normalized_error = ((spatial_error + abs_max) / (2 * abs_max)) * 255.0
                normalized_error = np.clip(normalized_error, 0, 255).astype(np.uint8)
                
                # Where mask is invalid, set to 127 (neutral)
                normalized_error[~valid_mask] = 127
                
                # Apply colormap (JET or coolwarm equivalent)
                # Jet: Blue (low/negative error), Green/Yellow (neutral/0 error), Red (high/positive error)
                heatmap = cv2.applyColorMap(normalized_error, cv2.COLORMAP_JET)
                
                # Set invalid areas to transparent/black if we want, but saving as JPG doesn't support alpha.
                # So we just leave them neutral green.
                
                cv2.imwrite(output_heatmap_path, heatmap)
                
                return {
                    "rmse": round(float(rmse), 2),
                    "mae": round(float(mae), 2)
                }
                
        except Exception as e:
            logger.error(f"[Validation Engine] Error during validation: {e}")
            raise
