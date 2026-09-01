import logging
import cv2
import numpy as np
import rasterio
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger("depth_wizard.ingestion")

class IngestionError(Exception):
    pass

class ImageIngestor:
    MAX_DIM = 2048

    @classmethod
    def load_image_and_metadata(cls, filepath: Path) -> Tuple[np.ndarray, Optional[Dict[str, Any]]]:
        """Loads an image into a normalized RGB numpy array and extracts spatial metadata."""
        if not filepath.exists():
            raise IngestionError(f"File not found: {filepath}")

        metadata = None
        try:
            with rasterio.open(filepath) as src:
                # Read as RGB (bands 1, 2, 3)
                img_array = src.read([1, 2, 3])
                # Transpose to HWC shape
                img_array = np.transpose(img_array, (1, 2, 0))
                
                # Check for spatial metadata
                if src.crs and src.transform:
                    metadata = {
                        "crs": src.crs.to_string(),
                        "transform": src.transform,
                        "bounds": {
                            "left": src.bounds.left,
                            "bottom": src.bounds.bottom,
                            "right": src.bounds.right,
                            "top": src.bounds.top
                        },
                        "width": src.width,
                        "height": src.height
                    }
                    logger.info(f"[Ingestion] Extracted metadata: CRS={metadata['crs']}")
                else:
                    logger.warning("[Ingestion] No CRS found in GeoTIFF, falling back to relative mode.")
        except rasterio.errors.RasterioIOError:
            # Fallback to OpenCV if rasterio fails (e.g. for standard PNG/JPG)
            logger.info("[Ingestion] rasterio failed, attempting standard OpenCV read.")
            img_array = cv2.imread(str(filepath))
            if img_array is None:
                raise IngestionError(f"Failed to read image data from {filepath}")
            # Convert BGR to RGB
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            metadata = None
            
        logger.info(f"[Ingestion] Loaded image shape: {img_array.shape}")
        
        # Enforce hardware constraints
        img_array = cls._validate_dimensions(img_array)
        return img_array, metadata

    @classmethod
    def _validate_dimensions(cls, image: np.ndarray) -> np.ndarray:
        """Enforces the 2048x2048 hard cap to prevent OOM errors."""
        h, w = image.shape[:2]
        if h > cls.MAX_DIM or w > cls.MAX_DIM:
            logger.warning(f"[Ingestion] Image dimensions {w}x{h} exceed cap. Downsampling to {cls.MAX_DIM} max.")
            scale = cls.MAX_DIM / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"[Ingestion] New image shape: {image.shape}")
        return image
