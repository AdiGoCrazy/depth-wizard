import numpy as np
import pytest
from depth_wizard.calibration import SRTMCalibrator, CalibrationFitError

def test_ransac_alignment():
    # Synthetic relative depth (0 to 1)
    relative_depth = np.linspace(0, 1, 1000).reshape((50, 20))
    # Synthetic absolute depth where true s=100 and t=50 (range 50 to 150)
    absolute_dem = relative_depth * 100 + 50
    
    scale, shift, metrics = SRTMCalibrator.align_and_regress(relative_depth, absolute_dem)
    
    # RANSAC should fit this perfectly
    assert np.isclose(scale, 100.0, rtol=0.1)
    assert np.isclose(shift, 50.0, rtol=0.1)
    assert metrics["r2_score"] > 0.95

def test_impossible_fit_raises_error():
    # If the DEM is completely inverted compared to relative depth
    relative_depth = np.linspace(0, 1, 1000).reshape((50, 20))
    absolute_dem = -relative_depth * 100 + 50 # Negative scale
    
    with pytest.raises(CalibrationFitError):
        SRTMCalibrator.align_and_regress(relative_depth, absolute_dem)
