import pytest
import numpy as np
from unittest.mock import patch

# These tests will fail/skip until Phase 3 development is complete
# We will create stubs assuming src.depth_wizard.preprocessing will exist

class TestImagePreprocessor:
    
    @pytest.fixture
    def preprocessor(self):
        try:
            from depth_wizard.preprocessing import ImagePreprocessor
            return ImagePreprocessor()
        except ImportError:
            pytest.skip("ImagePreprocessor not implemented yet (Phase 3 pending).")

    def test_apply_clahe_modifies_image(self, preprocessor):
        """Ensures CLAHE runs and alters the array without changing dimensions."""
        test_rgb = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        result = preprocessor.apply_clahe(test_rgb)
        
        assert result.shape == test_rgb.shape, "CLAHE altered image dimensions."
        assert result.dtype == test_rgb.dtype, "CLAHE altered image dtype."
        # The result should be mathematically distinct from the input
        assert not np.array_equal(result, test_rgb), "CLAHE did not modify the image."

    def test_enhance_shadows_darkens_pixels(self, preprocessor):
        """Ensures shadow enhancement successfully lowers the value of dark pixels."""
        # Create an image with a specific "dark" patch to simulate shadows
        test_rgb = np.ones((100, 100, 3), dtype=np.uint8) * 200  # Light gray
        test_rgb[40:60, 40:60] = [30, 30, 30]  # Very dark gray (simulated shadow)
        
        result = preprocessor.enhance_shadows(test_rgb)
        
        # Extract the shadow region
        original_shadow = test_rgb[40:60, 40:60]
        enhanced_shadow = result[40:60, 40:60]
        
        # The mean value of the shadow should be strictly less after enhancement
        assert np.mean(enhanced_shadow) < np.mean(original_shadow), "Shadows were not darkened."

    def test_invalid_dtype_handling(self, preprocessor):
        """Tests Threat Model: Dtype Casting Errors."""
        # Pass a float64 array, which OpenCV color space functions reject by default
        test_float = np.random.rand(100, 100, 3)
        
        with pytest.raises((ValueError, TypeError)):
            preprocessor.process(test_float)
