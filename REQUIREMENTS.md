# DepthWizard: Single-View Height Estimation & 3D Flythrough

> **ISRO Hackathon Problem Statement 26175**  
> **Theme:** Disaster Management  
> **Organization:** Indian Space Research Organisation (ISRO) / Space Applications Centre (SAC)  

---

## 1. Executive Summary & Problem Context

Accurate Digital Elevation Models (DEMs) and Digital Surface Models (DSMs) are essential for disaster management, flood modeling, urban planning, and military reconnaissance. Traditional methods (stereo-imaging pairs, LiDAR, InSAR) require expensive sensors, multiple passes, and heavy computation.

**DepthWizard** addresses these limitations by leveraging state-of-the-art Monocular Depth Estimation (MDE) models to reconstruct height maps from **single-view optical satellite/aerial RGB imagery**. It resolves the domain gap and scale ambiguity inherent in relative depth models by aligning predicted depths with coarse DEMs (e.g., SRTM 30m) or Ground Control Points (GCPs), outputting metric-scale GeoTIFF DSMs alongside an interactive 3D terrain flythrough engine.

---

## 2. Core Capabilities & Input/Output Matrix

| Input Format | Metadata | Target Output | Processing Pipeline |
| :--- | :--- | :--- | :--- |
| **Non-Georeferenced RGB** (`.png`, `.jpg`, `.jpeg`) | None (Pixel space) | **Relative DSM (rDSM)** (`.tiff`, `.png`) + 3D Mesh | Pre-trained MDE backbone $\rightarrow$ Relative depth normalization $\rightarrow$ 3D mesh rendering |
| **Georeferenced RGB** (`.tif`, `.geotiff`) | CRS, Transform, Bounding Box | **Absolute Metric DSM** (`.geotiff`) + 3D Mesh with Spatial Coordinates | Pre-trained MDE backbone $\rightarrow$ Metric Scale Calibration (SRTM / GCP fitting) $\rightarrow$ GeoTIFF export + 3D terrain rendering |

---

## 3. System Architecture & Component Breakdown

```
                      ┌──────────────────────────────────────────────┐
                      │    Input Satellite / Aerial RGB Image        │
                      │       (GeoTIFF / TIFF / PNG / JPG)           │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │     Ingestion & Metadata Parser Module       │
                      │  - Parses CRS, GeoTransform, GSD (if present)│
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │   Monocular Depth Estimation (MDE) Engine    │
                      │  - Backbone: Depth Anything v2 / Marigold    │
                      │  - Outputs relative depth map Z_rel          │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    Scale Calibration & Metric Alignment      │
                      │  - Fits Z_metric = s * Z_rel + t             │
                      │  - Anchor sources: SRTM 30m / GCPs / Prior   │
                      └──────────────────────┬───────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
┌─────────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐
│      Elevation Export & Analytics           │ │       Interactive 3D Flythrough             │
│ - Metric GeoTIFF DSM Export                 │ │ - Three.js / WebGL 3D Terrain Engine        │
│ - Slope & Aspect Map Computation            │ │ - Texture mapping of optical RGB            │
│ - Height Query & Profile Cross-section      │ │ - WASD + Mouse First-Person / Drone Cam     │
│ - Validation against Ground Truth (RMSE/MAE)│ │ - Point Inspector (Elevation, Slope)        │
└─────────────────────────────────────────────┘ └─────────────────────────────────────────────┘
```

---

## 4. Technical Requirements & Key Specifications

### 4.1 Elevation Estimation Module
* **Pre-trained MDE Model Integration:** Support for state-of-the-art monocular depth estimation backbones (e.g. `Depth-Anything-V2`, `Marigold`, `MiDaS`, or fine-tuned weights for satellite domain).
* **Format Support:** Standard raster formats (`.png`, `.jpg`, `.tif`, `.geotiff`).
* **Handling Geospatial Metadata:** Parse projection systems (EPSG codes, WGS84, UTM zones) using `rasterio` / `gdal`.

### 4.2 Scale Calibration & Metric Alignment Engine
* **Relative-to-Absolute Transformation:** Implement linear ($Z_{metric} = s \cdot Z_{rel} + t$) and non-linear / polynomial affine mapping.
* **Reference Sources for Calibration:**
  1. **Low-Resolution DEM Anchor:** Automate fetching/resampling of SRTM 30m or Copernicus 30m DEM for the target bounding box to solve for scale ($s$) and shift ($t$).
  2. **Ground Control Points (GCPs):** User-defined or file-imported 3D points $(X, Y, Z_{true})$.
  3. **Scene-Level Priors:** Sensor height, GSD, or statistical terrain bounds.

### 4.3 Interactive 3D Visualization Platform
* **Rendering Engine:** Web-based 3D terrain renderer powered by Three.js / WebGL / Deck.gl.
* **Terrain Mesh Projection:** Generate heightmap displacement mesh from estimated DSM and map the original high-res optical image as an RGB texture.
* **Navigation Modes:**
  * **Flythrough Camera:** WASD + Mouse FPS controls (pitch, yaw, elevation, speed boost).
  * **Free Orbit Camera:** 360-degree rotation around points of interest.
* **Interactive Tools:**
  * **Inspector Tool:** Hover/click on terrain to display exact metric elevation ($Z$), slope ($^\circ$), and spatial coordinates.
  * **Elevation Profile Tool:** Draw cross-section lines on the map to generate real-time 2D elevation profiles.
  * **Layer Toggles:** Switch between RGB optical view, colormapped DSM depth view, slope map, and error difference heatmap.

### 4.4 Accuracy Validation & Benchmarking Engine
* **Statistical Metrics:**
  * **RMSE (Root Mean Square Error):** $\sqrt{\frac{1}{N}\sum (Z_{pred} - Z_{gt})^2}$
  * **MAE (Mean Absolute Error):** $\frac{1}{N}\sum |Z_{pred} - Z_{gt}|$
  * **Correlation Coefficient ($R^2$ / Pearson $r$):** Measures linear structural agreement.
* **Terrain Categorization Breakdown:** Evaluate metric stability across urban, sparse, hilly, and forested landscapes.

---

## 5. Technology Stack

* **Backend & ML Pipeline:** Python 3.13, PyTorch, Open CV, `rasterio`, `gdal`, `scipy`, `numpy`, `uv`.
* **Depth Model Options:** `Depth-Anything-V2-Small/Base`, `Marigold-Depth`, or custom PyTorch remote sensing checkpoints.
* **Frontend & 3D Visualization:** Fast HTML5 / TypeScript / React or Vanilla JS interface with Three.js / WebGL, TailwindCSS / custom styling.
* **API / Backend Communication:** FastAPI / Flask server exposing endpoints for image upload, depth inference, DEM calibration, GeoTIFF generation, and mesh streaming.

---

## 6. Hackathon Deliverables Checklist

- [ ] **Data Pipeline & Inference Backend:** API to process non-georeferenced and georeferenced satellite images.
- [ ] **Scale Calibration Module:** SRTM / GCP linear alignment logic for metric DSM output.
- [ ] **GeoTIFF Generator:** Standard geospatial export with projection tags.
- [ ] **Interactive 3D Web UI:** Web browser interface with smooth flythrough, texture mapping, and inspection tools.
- [ ] **Validation Toolset:** Benchmark suite evaluating RMSE, MAE, and correlation against reference DEMs.
- [ ] **Documentation & Demo:** User guide, installation scripts, and presentation materials.
