import logging
import cv2
import numpy as np

logger = logging.getLogger("depth_wizard.preprocessing")

class ImagePreprocessor:
    def __init__(self, clahe_clip_limit: float = 2.0, shadow_threshold_percentile: int = 10, shadow_darken_factor: float = 0.5):
        self.clahe_clip_limit = clahe_clip_limit
        self.shadow_threshold_percentile = shadow_threshold_percentile
        self.shadow_darken_factor = shadow_darken_factor
        self.clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=(8, 8))
        logger.info("[ImagePreprocessor] Initialized stateless preprocessing pipeline.")

    def apply_clahe(self, rgb_image: np.ndarray) -> np.ndarray:
        """Applies CLAHE on the L-channel of the LAB color space."""
        logger.debug("[ImagePreprocessor] Applying CLAHE.")
        lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE to the lightness channel
        cl = self.clahe.apply(l_channel)
        
        merged_lab = cv2.merge((cl, a_channel, b_channel))
        return cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)

    def enhance_shadows(self, rgb_image: np.ndarray) -> np.ndarray:
        """Darkens the bottom Nth percentile of pixels in the HSV V-channel."""
        logger.debug("[ImagePreprocessor] Applying Shadow Enhancement.")
        hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)
        
        # Find the threshold for the darkest pixels
        threshold = np.percentile(v_channel, self.shadow_threshold_percentile)
        logger.debug(f"[ImagePreprocessor] Shadow threshold value (p{self.shadow_threshold_percentile}): {threshold:.2f}")
        
        # Darken pixels below the threshold
        mask = v_channel < threshold
        # Convert to float for multiplication to prevent uint8 underflow wrap-around
        v_float = v_channel.astype(np.float32)
        v_float[mask] = v_float[mask] * self.shadow_darken_factor
        
        # Re-assign and cast back to uint8
        v_channel = np.clip(v_float, 0, 255).astype(np.uint8)
        
        merged_hsv = cv2.merge((h_channel, s_channel, v_channel))
        return cv2.cvtColor(merged_hsv, cv2.COLOR_HSV2RGB)
        
    def process(self, rgb_image: np.ndarray) -> np.ndarray:
        """Chains the preprocessing methods sequentially."""
        if not isinstance(rgb_image, np.ndarray):
            raise TypeError("Input must be a numpy ndarray.")
        if rgb_image.dtype != np.uint8:
            raise ValueError(f"Input must be uint8, got {rgb_image.dtype}")
        if len(rgb_image.shape) != 3 or rgb_image.shape[2] != 3:
            raise ValueError(f"Input must be a 3-channel RGB image, got shape {rgb_image.shape}")
            
        logger.info("[ImagePreprocessor] Starting preprocessing pipeline...")
        processed = self.apply_clahe(rgb_image)
        processed = self.enhance_shadows(processed)
        logger.info("[ImagePreprocessor] Preprocessing complete.")
        return processed
