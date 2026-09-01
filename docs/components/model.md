# MDE Engine (`src/depth_wizard/model.py`)

## Purpose
Manages the PyTorch lifecycle for the `Depth Anything V2` backbone. Handles VRAM memory allocation securely and processes the RGB array to predict relative depth, including the shadow mitigation and guided filter band-aids.

## Key Classes & Functions
* `class DepthModel:`
  * `def __init__(checkpoint_size="Small"):` Initializes model. Maps to `cuda` if available, heavily profiling VRAM.
  * `def mitigate_shadows(image: np.ndarray) -> np.ndarray:` Pre-processes image in HSV space to lighten dark shadows.
  * `def predict(image: np.ndarray) -> np.ndarray:` Runs inference inside `torch.no_grad()` to prevent memory leaks.
  * `def guided_filter_refine(raw_depth: np.ndarray, guide_rgb: np.ndarray) -> np.ndarray:` Post-processing edge snapper.

## Inputs & Outputs
* **Input:** `np.ndarray` (RGB image, max 2048x2048).
* **Output:** `np.ndarray` (Relative Depth Map, normalized 0.0 to 1.0).

## Error Handling
* Catches `RuntimeError: CUDA out of memory` and triggers an automatic fallback to `cpu` or clears CUDA cache and raises a structured `ResourceExhaustedError`.
