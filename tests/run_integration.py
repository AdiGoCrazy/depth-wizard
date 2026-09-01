import cv2
import numpy as np
import io
import os
from pathlib import Path
from fastapi.testclient import TestClient

# We must mock the env vars before importing the API
os.environ["ASSET_STORAGE_DIR"] = "/tmp/depthwizard_exports"
from depth_wizard.api import app

def run_integration():
    print("--- Starting DepthWizard Backend Integration Test ---")
    
    # 1. Setup Test Client
    client = TestClient(app)
    
    # 2. Generate Synthetic 512x512 RGB Image
    print("[1] Generating synthetic 512x512 image...")
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    
    # Draw some shapes to simulate buildings and shadows
    cv2.rectangle(img, (100, 100), (200, 200), (200, 200, 200), -1) # Light building
    cv2.rectangle(img, (200, 100), (250, 200), (30, 30, 30), -1)     # Dark shadow
    cv2.circle(img, (400, 400), 50, (150, 150, 150), -1)             # Dome
    
    # Encode to JPEG in memory
    success, encoded_img = cv2.imencode('.jpg', img)
    if not success:
        raise Exception("Failed to encode synthetic image.")
    
    image_bytes = encoded_img.tobytes()
    
    # 3. Simulate Multipart Upload via TestClient
    print("[2] Triggering POST /api/process (This will download PyTorch weights if first run)...")
    files = {"file": ("test_upload.jpg", io.BytesIO(image_bytes), "image/jpeg")}
    
    response = client.post("/api/process", files=files)
    
    # 4. Verify HTTP Response
    print(f"[3] Received HTTP Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")
        assert False, "Pipeline failed."
        
    data = response.json()
    print(f"[4] Response JSON: {data}")
    
    # 5. Verify JSON Payload Expectations
    assert data["status"] == "success"
    assert data["is_metric"] is False # Because it's a JPG, no CRS bounds
    assert data["dsm_url"].startswith("/assets/")
    assert data["mesh_url"].startswith("/assets/")
    
    # 6. Verify Files Exist on Disk
    dsm_filename = data["dsm_url"].split("/assets/")[1]
    mesh_filename = data["mesh_url"].split("/assets/")[1]
    
    dsm_path = Path("/tmp/depthwizard_exports") / dsm_filename
    mesh_path = Path("/tmp/depthwizard_exports") / mesh_filename
    
    print(f"[5] Verifying {dsm_path} exists...")
    assert dsm_path.exists(), f"Missing DSM file at {dsm_path}"
    
    print(f"[6] Verifying {mesh_path} exists...")
    assert mesh_path.exists(), f"Missing Mesh file at {mesh_path}"
    
    print("--- ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_integration()
