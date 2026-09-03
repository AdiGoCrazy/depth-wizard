import os
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from depth_wizard.ingestion import ImageIngestor, IngestionError
from depth_wizard.preprocessing import ImagePreprocessor
from depth_wizard.model import DepthModel, ResourceExhaustedError
from depth_wizard.segmentation import SegmentationEngine, flatten_depth_by_masks
from depth_wizard.calibration import SRTMCalibrator, CalibrationFitError, CalibrationNetworkError
from depth_wizard.export import Exporter

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("depth_wizard.api")

app = FastAPI(title="DepthWizard Backend API")

# Setup Export Directory
ASSET_STORAGE_DIR = Path(os.getenv("ASSET_STORAGE_DIR", "/tmp/depthwizard_exports"))
ASSET_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(ASSET_STORAGE_DIR)), name="assets")

# Initialize long-lived components
preprocessor = ImagePreprocessor()
mde_engine = DepthModel(checkpoint_size="Small")
seg_engine = SegmentationEngine(device="cpu")
exporter = Exporter(export_dir=ASSET_STORAGE_DIR)

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

@app.post("/api/process")
async def process_image(file: UploadFile = File(...), environment: str = Form("urban")):
    logger.info(f"[API Gateway] Received upload request: {file.filename} (Environment: {environment})")
    
    # Validate environment payload
    if environment not in ["urban", "terrain"]:
        logger.warning(f"[API Gateway] Invalid environment '{environment}', falling back to 'urban'")
        environment = "urban"
    
    # 1. Size Validation (mocked check, FastAPI natively uses Starlette limits)
    # A robust check would read chunks or use Content-Length headers.
    
    # 2. Save uploaded file securely
    job_id = str(uuid.uuid4())
    temp_dir = ASSET_STORAGE_DIR / f"job_{job_id}"
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename
    
    try:
        with open(temp_file, "wb") as f:
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=413, detail="Payload Too Large (Max 20MB)")
            f.write(content)
            
        # Phase 1: Ingestion
        rgb_array, metadata = ImageIngestor.load_image_and_metadata(temp_file)
        
        # Phase 1.5: Preprocessing (CLAHE + Shadow Enhancement)
        if environment == "urban":
            logger.info("[API Gateway] Urban environment selected. Running preprocessing.")
            rgb_array = preprocessor.process(rgb_array)
        else:
            logger.info("[API Gateway] Terrain environment selected. Bypassing preprocessing.")
        
        # Phase 2: Depth Inference
        mde_engine.load_to_gpu()
        relative_depth = mde_engine.predict(rgb_array)
        mde_engine.unload_to_cpu()
        
        # Phase 2.5: Instance Segmentation & Edge Flattening
        if environment == "urban":
            logger.info("[API Gateway] Urban environment selected. Running segmentation.")
            seg_engine.load_to_gpu()
            masks = seg_engine.generate_masks(rgb_array)
            seg_engine.unload_to_cpu()
            
            if masks:
                relative_depth = flatten_depth_by_masks(relative_depth, masks)
        else:
            logger.info("[API Gateway] Terrain environment selected. Bypassing segmentation.")
        
        # Phase 3: Calibration & Export
        is_metric = False
        metrics = None
        final_dsm = relative_depth
        
        if metadata and "bounds" in metadata:
            try:
                # Fetch anchor
                srtm_anchor = SRTMCalibrator.fetch_srtm(metadata["bounds"], target_shape=relative_depth.shape)
                # Regress
                scale, shift, metrics = SRTMCalibrator.align_and_regress(relative_depth, srtm_anchor)
                # Apply
                final_dsm = SRTMCalibrator.apply_calibration(relative_depth, scale, shift)
                is_metric = True
            except (CalibrationFitError, CalibrationNetworkError) as e:
                logger.warning(f"[API Gateway] Calibration failed, falling back to relative. Error: {e}")
                
        # Export Assets
        dsm_filename = f"{job_id}_dsm.tif"
        mesh_filename = f"{job_id}_mesh.json"
        texture_filename = f"{job_id}_texture.jpg"
        
        # If the DSM is relative (0.0 to 1.0 float), scale it to 8-bit (0-255)
        # so generic image viewers don't render it completely white/black.
        import numpy as np
        if not is_metric:
            export_dsm = (final_dsm * 255.0).astype(np.uint8)
        else:
            export_dsm = final_dsm
            
        exporter.export_geotiff(export_dsm, metadata or {}, dsm_filename)
        exporter.export_mesh_data(final_dsm, mesh_filename)
        exporter.export_texture(rgb_array, texture_filename)
        
        return JSONResponse(content={
            "status": "success",
            "job_id": job_id,
            "is_metric": is_metric,
            "dsm_url": f"/assets/{dsm_filename}",
            "mesh_url": f"/assets/{mesh_filename}",
            "texture_url": f"/assets/{texture_filename}",
            "metrics": metrics
        })
        
    except HTTPException as he:
        raise he
    except IngestionError as ie:
        logger.error(f"Ingestion failed: {ie}")
        raise HTTPException(status_code=400, detail="Invalid image file or format.")
    except ResourceExhaustedError as re:
        logger.error(f"VRAM Exhausted: {re}")
        raise HTTPException(status_code=507, detail="Server resources exhausted. Image too large.")
    except Exception as e:
        logger.error(f"Internal Pipeline Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        # Cleanup temporary uploaded file (do not clean up generated assets here)
        if temp_file.exists():
            temp_file.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()

from depth_wizard.validation import ValidationEngine

@app.post("/api/validate")
async def validate_dsm(file: UploadFile = File(...), job_id: str = Form(...)):
    logger.info(f"[API Gateway] Received validation request for Job ID: {job_id}")
    
    predicted_dsm_path = ASSET_STORAGE_DIR / f"{job_id}_dsm.tif"
    if not predicted_dsm_path.exists():
        raise HTTPException(status_code=404, detail="Predicted DSM not found for this Job ID.")
        
    # Save the GT file temporarily
    gt_temp_path = ASSET_STORAGE_DIR / f"{job_id}_gt_{file.filename}"
    try:
        with open(gt_temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        heatmap_filename = f"{job_id}_heatmap.jpg"
        heatmap_path = ASSET_STORAGE_DIR / heatmap_filename
        
        metrics = ValidationEngine.calculate_metrics_and_heatmap(
            str(predicted_dsm_path), 
            str(gt_temp_path), 
            str(heatmap_path)
        )
        
        return JSONResponse(content={
            "status": "success",
            "rmse": metrics["rmse"],
            "mae": metrics["mae"],
            "heatmap_url": f"/assets/{heatmap_filename}"
        })
    except Exception as e:
        logger.error(f"[API Gateway] Validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if gt_temp_path.exists():
            gt_temp_path.unlink()

# Mount Frontend Static Directory (Must be defined AFTER API routes to prevent fallback shadowing)
FRONTEND_DIR = Path(__file__).parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
