import numpy as np
import pytest
import cv2
from pathlib import Path
from depth_wizard.ingestion import ImageIngestor, IngestionError

def test_dimensions_validation():
    # Create an artificially massive mock image 3000x2000
    massive_image = np.zeros((3000, 2000, 3), dtype=np.uint8)
    
    validated = ImageIngestor._validate_dimensions(massive_image)
    
    h, w = validated.shape[:2]
    assert h <= 2048
    assert w <= 2048
    assert h == 2048 # scaled down on largest axis
    assert w == int(2000 * (2048/3000))

def test_missing_file_raises_error():
    with pytest.raises(IngestionError):
        ImageIngestor.load_image_and_metadata(Path("non_existent_file.tif"))
