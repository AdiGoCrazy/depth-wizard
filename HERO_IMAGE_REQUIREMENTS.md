# Hero Image Selection Requirements

To ensure a flawless prototype presentation of **DepthWizard**, we must carefully curate the satellite images used for the live demonstration. 

Because we are utilizing a zero-shot foundation model (Depth Anything V2), we have applied some *band-aid solutions* to limitations that cannot be structurally fixed within the hackathon timeframe. The criteria below ensure we select images that **do not trigger those specific limitations**, guaranteeing a perfect, "wow-factor" presentation.

---

## 1. Visual & Environmental Criteria (Bypassing Limitations)

These requirements are specifically designed to avoid edge cases that confuse the depth model.

* **Strictly Cloud-Free & Haze-Free (Avoids Atmospheric Artifacts):**
  * **Requirement:** The image crop must have absolutely **0% cloud cover** and minimal atmospheric haze/smog.
  * **Why:** The model interprets white, milky clouds or heavy haze as physical floating geometry. We must bypass this entirely by using perfectly clear imagery.
* **True Nadir Perspective (Avoids Domain Shift Confusion):**
  * **Requirement:** Imagery must be **orthorectified** (looking straight down).
  * **Why:** If the image is taken at an oblique angle where building facades (walls) are highly visible, the model's perspective engine gets confused and may slant the buildings. True nadir forces the model to rely purely on roof edges and shadows.
* **High Geometric & Color Contrast (Avoids Flat Blending):**
  * **Requirement:** Select urban areas where rooftops are a distinctly different color or texture than the surrounding ground (e.g., white concrete/red tile roofs on dark asphalt).
  * **Why:** Depth models struggle to separate flat surfaces that blend together visually. High contrast allows our *Guided Filter* band-aid solution to easily snap depth edges perfectly to the building outlines.
* **Avoid Large Reflective Surfaces (Avoids Specular "Holes"):**
  * **Requirement:** Avoid scenes dominated by glaring bodies of water, snow cover, or massive mirror-glass skyscrapers reflecting the sun.
  * **Why:** Specular highlights and reflections often trick depth estimators into predicting infinite depth (rendering as a deep trench).

---

## 2. Technical & Format Requirements

To ensure our ingestion, calibration, and 3D visualization pipelines run smoothly and quickly during the live demo.

* **Primary File Format:** **GeoTIFF (`.tif` / `.geotiff`)**
  * Essential for demonstrating the exact metric Scale Calibration engine.
* **Geospatial Metadata:**
  * Must contain a standard embedded **CRS (Coordinate Reference System)**—preferably WGS84 (EPSG:4326) or a local UTM Zone.
  * Must contain exact **GeoTransform bounding box coordinates** so our pipeline can automatically download the overlapping SRTM 30m calibration DEM.
* **Spatial Resolution (Ground Sample Distance):**
  * **0.1m to 0.5m / pixel (Sub-meter).**
  * Very high resolution (drone or premium satellite imagery like Maxar/Planet SkySat) is required so the model can resolve crisp building edges. (Avoid 10m Sentinel-2 imagery for the Hero demo, as it is too low-res for impressive 3D structural flythroughs).
* **Dimensions (Pixel Size):**
  * **Recommendation:** Pre-crop the images to **1024 x 1024** or **2048 x 2048** pixels.
  * **Why:** 
    1. It balances stunning high-res detail with fast, real-time inference speeds during a live pitch.
    2. Model architectures (Vision Transformers) perform best on dimensions divisible by 14.

---

## 3. The Recommended "Hero" Scenes

When sourcing data, we should find exactly two datasets that fit the criteria above:

### Scene A: The Urban Structural Showcase
* **Target:** A dense, modern downtown area (e.g., Dubai, Manhattan, or a highly structured ISRO campus) with blocky, distinct skyscrapers.
* **Presentation Goal:** Demonstrates the model's ability to pull distinct vertical structures from the ground and our ability to calibrate them to exact metric building heights.

### Scene B: The Rugged Terrain Showcase
* **Target:** A sharp mountainous region, deep canyon, or distinct geological formation without snow cover (e.g., the Grand Canyon, barren Himalayan valleys).
* **Presentation Goal:** Demonstrates smooth, flowing topographical elevation mapping and how well the Three.js 3D flythrough handles massive terrain scale.
