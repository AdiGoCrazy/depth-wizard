import logging
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from transformers import pipeline
from pathlib import Path
from PIL import Image
import gc

logger = logging.getLogger("depth_wizard.model")

class ResourceExhaustedError(Exception):
    pass

class DepthModel:
    def __init__(self, checkpoint_size="Small"):
        # Explicit memory tracking and device assignment
        # We strictly initialize on CPU so the model does not hold VRAM hostage while idle.
        # It will be swapped to GPU on demand by the orchestrator.
        self.device = torch.device("cpu")
        logger.info(f"[MDE Engine] Initializing Depth Anything V2 {checkpoint_size} on {self.device} (VRAM Swapped out)")
        
        self.is_on_gpu = False
        
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

    def load_to_gpu(self):
        """Moves the model to GPU if not already there."""
        if torch.cuda.is_available() and not self.is_on_gpu:
            logger.info("[MDE Engine] Moving Depth Anything V2 to GPU (CUDA)")
            self.pipe.model.to('cuda')
            self.device = torch.device('cuda')
            self.pipe.device = self.device
            self.is_on_gpu = True

    def unload_to_cpu(self):
        """Moves the model to CPU and frees VRAM."""
        if self.is_on_gpu:
            logger.info("[MDE Engine] Moving Depth Anything V2 to CPU and clearing CUDA cache")
            self.pipe.model.to('cpu')
            self.device = torch.device('cpu')
            self.pipe.device = self.device
            self.is_on_gpu = False
            
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()



    def predict(self, image: np.ndarray) -> np.ndarray:
        """Runs inference inside no_grad to strictly cap memory."""
        logger.info("[MDE Engine] Starting depth prediction...")
        
        try:
            with torch.no_grad():
                # Run actual Depth Anything V2 inference via HuggingFace
                pil_img = Image.fromarray(image)
                result = self.pipe(pil_img)
                
                # The output contains a 'depth' key which is a PIL Image scaled 0-255
                depth_np = np.array(result['depth']).astype(np.float32)
                
                # Normalize 0 to 1
                depth_min = depth_np.min()
                depth_max = depth_np.max()
                depth_np = (depth_np - depth_min) / (depth_max - depth_min + 1e-8)
                
            logger.info("[MDE Engine] Inference complete.")
            return depth_np
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                logger.error("[MDE Engine] CUDA OOM caught. Clearing cache.")
                torch.cuda.empty_cache()
                raise ResourceExhaustedError("Failed due to VRAM limitations. Image too large.")
            raise e
