import logging
import rasterio
from rasterio.transform import from_bounds
import numpy as np
from pathlib import Path
import json

logger = logging.getLogger("depth_wizard.export")

class Exporter:
    def __init__(self, export_dir: Path):
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    def export_geotiff(self, dsm: np.ndarray, metadata: dict, filename: str) -> Path:
        """Exports the absolute DSM array to a standardized GeoTIFF."""
        output_path = self.export_dir / filename
        logger.info(f"[Export] Writing GeoTIFF to {output_path}")
        
        try:
            # Reconstruct transform if bounds exist
            bounds = metadata.get("bounds")
            transform = metadata.get("transform")
            crs = metadata.get("crs")
            
            h, w = dsm.shape
            
            if not transform and bounds:
                transform = from_bounds(
                    bounds["left"], bounds["bottom"], bounds["right"], bounds["top"], w, h
                )

            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=h,
                width=w,
                count=1,
                dtype=dsm.dtype,
                crs=crs,
                transform=transform,
                compress='lzw'
            ) as dst:
                dst.write(dsm, 1)
                
            return output_path
        except Exception as e:
            logger.error(f"[Export] Failed to export GeoTIFF: {e}")
            raise IOError(f"GeoTIFF export failed: {e}")

    def export_mesh_data(self, dsm: np.ndarray, filename: str) -> Path:
        """Exports heightmap data tailored for Three.js rendering."""
        output_path = self.export_dir / filename
        logger.info(f"[Export] Exporting JSON mesh data to {output_path}")
        
        # Downsample for web if too large
        import cv2
        MAX_WEB_DIM = 256
        h, w = dsm.shape
        if h > MAX_WEB_DIM or w > MAX_WEB_DIM:
            scale = MAX_WEB_DIM / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            dsm = cv2.resize(dsm, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Convert to list for JSON serialization
        mesh_data = {
            "width": dsm.shape[1],
            "height": dsm.shape[0],
            "min_height": float(np.min(dsm)),
            "max_height": float(np.max(dsm)),
            "height_data": dsm.flatten().tolist()
        }
        
        with open(output_path, 'w') as f:
            json.dump(mesh_data, f)
            
        return output_path

    def export_texture(self, rgb_array: np.ndarray, filename: str) -> Path:
        """Exports the RGB array to a web-compatible image format (e.g. JPG)."""
        from PIL import Image
        output_path = self.export_dir / filename
        logger.info(f"[Export] Exporting texture to {output_path}")
        
        # Downsample for web if too large to match mesh or keep some high res
        # For texture, we can keep it up to 2048x2048
        img = Image.fromarray(rgb_array)
        img.save(output_path, format='JPEG', quality=85)
        
        return output_path
