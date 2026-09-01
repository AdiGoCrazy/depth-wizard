import pytest
from unittest.mock import patch, MagicMock

# These tests will fail/skip until Phase 3 development is complete
# We will create stubs assuming src.depth_wizard.api will be updated

class TestAPIGatewayEnvironmentToggle:
    
    @pytest.fixture
    def mock_app(self):
        try:
            from fastapi.testclient import TestClient
            from depth_wizard.api import app
            return TestClient(app)
        except ImportError:
            pytest.skip("API routing logic not implemented yet (Phase 3 pending).")

    @patch("depth_wizard.api.mde_engine.predict")
    @patch("depth_wizard.api.ImageIngestor.load_image_and_metadata")
    @patch("depth_wizard.api.preprocessor.process")
    @patch("depth_wizard.api.seg_engine.generate_masks")
    def test_environment_urban_triggers_full_pipeline(self, mock_seg, mock_prep, mock_ingest, mock_mde, mock_app):
        """Ensures 'urban' environment runs the preprocessor and FastSAM."""
        import numpy as np
        fake_img = np.zeros((10, 10, 3), dtype=np.uint8)
        mock_ingest.return_value = (fake_img, {})
        mock_prep.return_value = fake_img
        mock_mde.return_value = np.zeros((10, 10), dtype=np.float32)
        mock_seg.return_value = []
        
        # Mock file upload
        test_file = {"file": ("test.png", b"fake_image_data", "image/png")}
        data = {"environment": "urban"}
        
        mock_app.post("/api/process", files=test_file, data=data)
        mock_prep.assert_called()
        mock_seg.assert_called()

    @patch("depth_wizard.api.mde_engine.predict")
    @patch("depth_wizard.api.ImageIngestor.load_image_and_metadata")
    @patch("depth_wizard.api.preprocessor.process")
    @patch("depth_wizard.api.seg_engine.generate_masks")
    def test_environment_terrain_bypasses_conflicting_modules(self, mock_seg, mock_prep, mock_ingest, mock_mde, mock_app):
        """Ensures 'terrain' environment strictly BYPASSES preprocessor and FastSAM."""
        import numpy as np
        fake_img = np.zeros((10, 10, 3), dtype=np.uint8)
        mock_ingest.return_value = (fake_img, {})
        mock_mde.return_value = np.zeros((10, 10), dtype=np.float32)
        
        # Mock file upload
        test_file = {"file": ("test.png", b"fake_image_data", "image/png")}
        data = {"environment": "terrain"}
        
        mock_app.post("/api/process", files=test_file, data=data)
        mock_prep.assert_not_called()
        mock_seg.assert_not_called()

    def test_invalid_environment_payload(self, mock_app):
        """Ensures API gracefully handles missing or invalid environment strings."""
        test_file = {"file": ("test.png", b"fake_image_data", "image/png")}
        data = {"environment": "city"} # Invalid
        
        response = mock_app.post("/api/process", files=test_file, data=data)
        
        # It should either default to urban (200) or reject the payload (422)
        # If it defaults to urban and tries to ingest fake data, it gets 400, which is also a graceful failure (not a 500 crash)
        assert response.status_code in [200, 400, 422], "API crashed on invalid environment payload."
