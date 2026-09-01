import logging
import gc
import torch
import numpy as np
from ultralytics import FastSAM

logger = logging.getLogger("depth_wizard.segmentation")

class SegmentationEngine:
    def __init__(self, device: str = "cpu"):
        self.device = device
        logger.info("[SegmentationEngine] Initializing FastSAM on CPU (VRAM Swapped out by default)")
        
        # Load FastSAM weights (ultralytics will auto-download FastSAM-s.pt if missing)
        # FastSAM is a CNN (YOLOv8-based) which avoids the massive VRAM spikes of ViT dense point grids.
        self.model = FastSAM('FastSAM-s.pt')
        self.model.to('cpu')
        
        # Track state
        self.is_on_gpu = False

    def load_to_gpu(self):
        """Moves the model weights from system RAM to CUDA."""
        if torch.cuda.is_available() and not self.is_on_gpu:
            logger.info("[SegmentationEngine] Moving FastSAM to GPU (CUDA)")
            self.model.to('cuda')
            self.is_on_gpu = True

    def unload_to_cpu(self):
        """Moves the model back to system RAM and forcefully clears CUDA cache."""
        if self.is_on_gpu:
            logger.info("[SegmentationEngine] Moving FastSAM to CPU and clearing CUDA cache")
            self.model.to('cpu')
            self.is_on_gpu = False
            
            # Aggressive VRAM cleanup
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def generate_masks(self, rgb_image: np.ndarray) -> list[np.ndarray]:
        """Runs the FastSAM everything-generator over the image."""
        if not self.is_on_gpu and torch.cuda.is_available():
            logger.warning("[SegmentationEngine] Generating masks while model is on CPU. This will be slow!")
            
        logger.info(f"[SegmentationEngine] Running FastSAM inference on image shape {rgb_image.shape}")
        
        # Run inference (segment everything)
        # Ultralytics SAM wrapper automatically segments everything if no prompts are given
        results = self.model(rgb_image, verbose=False)
        
        masks_list = []
        if len(results) > 0 and results[0].masks is not None:
            # masks.data is a tensor of shape (N, H, W)
            # Move to CPU, convert to numpy bool array
            masks_tensor = results[0].masks.data.cpu().numpy()
            for i in range(masks_tensor.shape[0]):
                masks_list.append(masks_tensor[i].astype(bool))
                
        logger.info(f"[SegmentationEngine] Generated {len(masks_list)} distinct polygon masks.")
        return masks_list

def flatten_depth_by_masks(depth_map: np.ndarray, masks: list[np.ndarray]) -> np.ndarray:
    """
    Applies strict 90-degree boundaries by flattening the depth values inside each mask.
    This eliminates the 'depth bleeding' blob effect.
    """
    flattened_depth = depth_map.copy()
    
    logger.info(f"[SegmentationEngine] Flattening depth map using {len(masks)} masks...")
    
    for mask in masks:
        # Resize mask to match depth_map if they differ (they shouldn't, but safety first)
        if mask.shape != depth_map.shape:
            import cv2
            mask = cv2.resize(mask.astype(np.uint8), (depth_map.shape[1], depth_map.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
            
        region_depths = flattened_depth[mask]
        
        if len(region_depths) < 10:  # Ignore microscopic noise masks
            continue
            
        # Calculate variance to see if this is a structural object with depth bleeding,
        # or just a flat piece of ground.
        variance = np.var(region_depths)
        
        # Only flatten if there is significant variance (indicating a structure that bled)
        # We use a threshold of 0.001 (for normalized 0-1 depth maps) or 1.0 (for absolute meters)
        # Since this happens after relative mapping but before calibration, depth is usually 0-1.
        if variance > 0.0001: 
            # Use the 90th percentile to represent the "true" roof height, avoiding the bleeding edges
            roof_height = np.percentile(region_depths, 90)
            flattened_depth[mask] = roof_height

    return flattened_depth
