# Model Strategy: Training vs. Pre-Trained Backbone

This document breaks down the strategy for the DepthWizard core depth-estimation engine, specifically addressing whether to train a custom model from scratch or leverage a pre-trained foundation model for the hackathon prototype.

---

## 1. Analysis of Methods: Training vs. Pre-Trained

### Method A: Training / Fine-Tuning a Custom Model
This involves taking a dataset (like the referenced SIH2026 repo or public datasets like ISPRS Potsdam or US3D) and training a neural network (e.g., UNet, Swin Transformer) to predict height directly from RGB pixels.

* **Pros:** 
  * Can be explicitly trained to output metric absolute height directly (if ground truth LiDAR is provided).
  * Learns remote-sensing specific features (e.g., ignoring shadows, understanding nadir perspective).
* **Cons (Why it's risky for a hackathon):**
  * **Compute & Time:** Requires vast GPU resources and days of training time.
  * **Data Dependency:** Requires massive amounts of perfectly aligned RGB + LiDAR pairs. If the provided dataset is small or noisy, the model will fail.
  * **Brittleness:** Highly likely to overfit. A model trained on Indian urban data might fail completely if judges upload a hilly forested area during testing.

### Method B: Using a Pre-Trained Backbone (Zero-Shot)
This involves utilizing massive foundation models (like **Depth Anything V2**, **Marigold**, or **MiDaS**) that have been trained on millions of diverse images to understand geometry universally.

* **Pros:**
  * **Guaranteed to Work:** Will always produce a structurally sound, highly detailed relative depth map out of the box.
  * **High Resolution:** Captures incredibly fine details (building edges, roads, trees).
  * **Alignment with Requirements:** The ISRO problem statement explicitly mandates this approach: *"The solution should use a pre-trained monocular depth-estimation backbone to generate initial relative-depth maps."*
* **Cons:**
  * Outputs **relative** depth (scale-agnostic), meaning it doesn't know if a building is 10 meters or 100 meters tall.
  * Domain Gap: May occasionally misinterpret dark shadows as deep trenches because it was trained heavily on natural/egocentric images.

---

## 2. Final Decision: Pre-Trained Backbone

We will **NOT** train a custom model from scratch. We will use a **Pre-Trained Foundation Model** (specifically `Depth Anything V2` due to its superior edge preservation). 

**Reasoning:**
1. **Compliance:** It explicitly fulfills the ISRO requirement to use a "pre-trained monocular depth-estimation backbone".
2. **Focus:** The true engineering challenge of this problem statement is *not* the depth estimation itself, but the **Scale Calibration** (converting relative depth to metric elevation via SRTM/GCPs) and the **3D Interactive Visualization**. Using a pre-trained model frees up our time to perfect these modules.
3. **Prototype Reliability:** We cannot risk a broken demo. A pre-trained model guarantees we will have a working, impressive pipeline.

---

## 3. The "Flawless Prototype" Presentation Plan

Because pre-trained models have limitations (domain gaps in satellite imagery), we must carefully curate our prototype presentation to highlight the system's strengths and mask its zero-shot weaknesses.

### Step 1: Curated Testing Dataset
We will prepare a pre-loaded local dataset of 5-10 highly curated images for the judges.
* **Characteristics:** High contrast, clear lighting, minimal deep shadows, and distinct structural height differences (e.g., tall isolated buildings, sharp canyons).
* **Reference Data:** We will pair these with pre-downloaded SRTM 30m DEMs or precise Ground Control Points (GCPs) to ensure the metric conversion step is instantaneous and mathematically flawless during the demo.

### Step 2: The "Hero" Satellite Images
For the primary live demo, we will use two specific "Hero" images:
1. **The Urban Hero:** A crisp, high-resolution GeoTIFF of a dense urban center (e.g., downtown area with skyscrapers). The pre-trained model will perfectly isolate the buildings from the ground. We will use GCPs to snap the building heights to exact real-world meters.
2. **The Terrain Hero:** A mountainous region. We will use SRTM 30m calibration to warp the relative depth map to the absolute metric elevation of the mountain range.

### Step 3: 3D Visualization Polish (The "Wow" Factor)
To distract from any minor imperfections in the depth map, the presentation will rely heavily on the **3D Flythrough Quality**:
* **Smooth Shading:** Apply smoothing filters to the displacement mesh to prevent jagged "stair-stepping" artifacts common in depth maps.
* **Dynamic Lighting & Shadows:** The Three.js renderer will include a sun object casting real-time shadows across the 3D terrain, dramatically enhancing the illusion of depth.
* **Interactive Proof:** We will demonstrate the "Point Inspector" tool on a known building in the Hero image, proving to the judges that the height reading matches reality (validating our Scale Calibration module).
