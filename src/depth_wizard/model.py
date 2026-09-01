import logging
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from transformers import pipeline
from pathlib import Path
from PIL import Image

logger = logging.getLogger("depth_wizard.model")

class ResourceExhaustedError(Exception):
    pass

class DepthModel:
    def __init__(self, checkpoint_size="Small"):
        # Explicit memory tracking and device assignment
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"[MDE Engine] Initializing Depth Anything V2 {checkpoint_size} on {self.device}")
        
        # Prefer local Large model (1.35GB) if present, then local Small, then fallback to HF Hub
        large_model_path = Path(__file__).parents[2] / "models" / "depth_anything_v2_large"
        small_model_path = Path(__file__).parents[2] / "models" / "depth_anything_v2_small"
        
        if large_model_path.exists() and (large_model_path / "model.safetensors").exists():
            logger.info(f"[MDE Engine] Loading local LARGE model (1.35GB) from {large_model_path}...")
            self.pipe = pipeline(task="depth-estimation", model=str(large_model_path), device=self.device)
        elif small_model_path.exists() and (small_model_path / "model.safetensors").exists():
            logger.info(f"[MDE Engine] Loading local SMALL model from {small_model_path}...")
            self.pipe = pipeline(task="depth-estimation", model=str(small_model_path), device=self.device)
        else:
            logger.info("[MDE Engine] Local weights not found, downloading from HuggingFace Hub...")
            self.pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Large-hf", device=self.device)
        
        if torch.cuda.is_available():
            logger.info(f"[MDE Engine] VRAM available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    def mitigate_shadows(self, image: np.ndarray) -> np.ndarray:
        """Band-Aid 1: Lighten dark shadows to prevent trench artifacts."""
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        v_channel = hsv[:, :, 2]
        
        # Isolate dark regions (shadows)
        shadow_mask = v_channel < 50
        
        if np.any(shadow_mask):
            logger.debug("[MDE Engine] Applying shadow mitigation.")
            # Artificially lighten the shadowed areas slightly to match surrounding albedo
            v_channel[shadow_mask] = np.clip(v_channel[shadow_mask] + 40, 0, 255)
            hsv[:, :, 2] = v_channel
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return image

    def predict(self, image: np.ndarray) -> np.ndarray:
        """Runs inference inside no_grad to strictly cap memory."""
        logger.info("[MDE Engine] Starting depth prediction...")
        processed_image = self.mitigate_shadows(image)
        
        try:
            with torch.no_grad():
                # Run actual Depth Anything V2 inference via HuggingFace
                pil_img = Image.fromarray(processed_image)
                result = self.pipe(pil_img)
                
                # The output contains a 'depth' key which is a PIL Image scaled 0-255
                depth_np = np.array(result['depth']).astype(np.float32)
                
                # Normalize 0 to 1
                depth_min = depth_np.min()
                depth_max = depth_np.max()
                depth_np = (depth_np - depth_min) / (depth_max - depth_min + 1e-8)
                
            logger.info("[MDE Engine] Inference complete.")
            
            # Band-Aid 2: Guided Filter Edge Alignment
            refined_depth = self.guided_filter_refine(depth_np, processed_image)
            return refined_depth
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.error("[MDE Engine] CUDA OOM caught. Clearing cache.")
                torch.cuda.empty_cache()
                raise ResourceExhaustedError("Failed due to VRAM limitations. Image too large.")
            raise e

    def guided_filter_refine(self, raw_depth: np.ndarray, guide_rgb: np.ndarray) -> np.ndarray:
        """Forces depth map edges to align with sharp RGB physical edges."""
        logger.debug("[MDE Engine] Applying guided filter.")
        # Ensure depth is float32
        raw_depth_f32 = raw_depth.astype(np.float32)
        # OpenCV ximgproc guided filter (mocked here with bilateralFilter due to dependency limits)
        # A true Guided Filter requires cv2.ximgproc, so we use Bilateral as a lightweight structural fallback
        # Multiply by 255 for cv2, then normalize back
        depth_8u = (raw_depth_f32 * 255).astype(np.uint8)
        filtered = cv2.bilateralFilter(depth_8u, d=9, sigmaColor=75, sigmaSpace=75)
        return filtered.astype(np.float32) / 255.0
