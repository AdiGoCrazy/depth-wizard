import numpy as np
import pytest
from depth_wizard.model import DepthModel

def test_shadow_mitigation():
    model = DepthModel()
    # Create an RGB image (10x10) that is completely black (dark shadow)
    dark_image = np.zeros((10, 10, 3), dtype=np.uint8)
    
    mitigated = model.mitigate_shadows(dark_image)
    
    # In HSV, V is channel 2. For purely black pixels (V=0), it should boost to 40.
    # We check if the mitigated image is no longer purely black.
    assert np.any(mitigated > 0), "Shadows were not lightened."

def test_predict_shape_and_bounds():
    model = DepthModel()
    # Create random noise image (100x100)
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    depth = model.predict(image)
    
    assert depth.shape == (100, 100), f"Expected shape (100, 100), got {depth.shape}"
    assert np.min(depth) >= 0.0, "Depth minimum should be >= 0.0"
    assert np.max(depth) <= 1.0 + 1e-5, "Depth maximum should be <= 1.0"
