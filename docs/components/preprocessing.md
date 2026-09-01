# ImagePreprocessor Component

**Path:** `src/depth_wizard/preprocessing.py`

## Purpose
The `ImagePreprocessor` component acts as a filter layer between raw ingestion and AI inference. Its sole purpose is to mathematically manipulate the pixel values of nadir satellite imagery to emphasize the features (sharp edges, dark shadows, high contrast) that zero-shot monocular depth models and segmentation networks rely on.

## Core Responsibilities
-   **CLAHE (Contrast Limited Adaptive Histogram Equalization):** Convert images to the LAB color space and apply local histogram equalization to the L (Lightness) channel to create stark visual separation between structures (e.g., roofs) and terrain.
-   **Shadow Enhancement:** Convert images to the HSV color space and artificially darken the V (Value) channel for pixels that are already dark, forcing the AI to interpret them as deep physical drops.
-   **Stateless Execution:** Operate entirely ephemerally on CPU RAM. The preprocessor holds no internal state between API requests and does not allocate any VRAM.

## Interface (Draft)
```python
class ImagePreprocessor:
    def __init__(self, clahe_clip_limit: float = 2.0, shadow_threshold_percentile: int = 10):
        pass

    def apply_clahe(self, rgb_image: np.ndarray) -> np.ndarray:
        """Applies CLAHE on the L-channel of the LAB color space."""
        pass

    def enhance_shadows(self, rgb_image: np.ndarray) -> np.ndarray:
        """Darkens the bottom Nth percentile of pixels in the HSV V-channel."""
        pass
        
    def process(self, rgb_image: np.ndarray) -> np.ndarray:
        """Chains the preprocessing methods sequentially."""
        pass
```

## Security & Data Integrity
-   **Input Validation:** The component must rigorously assert that the incoming payload is a valid 3-channel `np.ndarray` of dtype `uint8`. If float data is passed, it must fail safely or cast properly to avoid OpenCV crashing the server.

## Logging Strategy
-   `INFO`: Report when preprocessing begins and ends.
-   `DEBUG`: Report the calculated threshold values used to identify the darkest pixels.
-   `ERROR`: Catch and report invalid matrix shapes or OpenCV C++ assertion failures.
