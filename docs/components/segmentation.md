# SegmentationEngine Component

**Path:** `src/depth_wizard/segmentation.py`

## Purpose
The `SegmentationEngine` is responsible for generating instance segmentation masks (polygons) of distinct physical structures (like buildings) from top-down optical satellite imagery. It utilizes a micro-architecture variant of the Segment Anything Model (MobileSAM) to guarantee a minimal memory footprint.

## Core Responsibilities
- **Initialization & Weight Management:** Load MobileSAM weights efficiently. If the weights do not exist locally, download them dynamically.
- **VRAM Swapping Protocol:** Expose specific `.load_to_gpu()` and `.unload_to_cpu()` methods to allow the pipeline orchestrator to safely swap this model out of VRAM when not in use.
- **Zero-Shot Inference:** Accept an RGB numpy array and return a list of binary masks representing distinct objects.

## Interface (Draft)
```python
class SegmentationEngine:
    def __init__(self, device: str = "cpu"):
        pass

    def load_to_gpu(self):
        """Moves the model weights from system RAM to CUDA."""
        pass

    def unload_to_cpu(self):
        """Moves the model back to system RAM and forcefully clears CUDA cache."""
        pass
        
    def generate_masks(self, rgb_image: np.ndarray) -> list[np.ndarray]:
        """Runs the MobileSAM everything-generator over the image."""
        pass
```

## Logging Strategy
- `INFO`: Report initialization and loading/unloading actions.
- `DEBUG`: Report the exact millisecond timing of PCI-E transfers during VRAM swaps.
- `ERROR`: Catch and report CUDA OOM errors explicitly.
