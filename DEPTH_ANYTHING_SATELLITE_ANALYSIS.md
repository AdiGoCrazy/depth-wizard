# Depth Anything V2: Satellite Imagery Limitations & Mitigation Strategy

As requested, this document outlines the research on using **Depth Anything V2** (a state-of-the-art zero-shot monocular depth estimation foundation model) specifically for satellite/aerial imagery. 

While it is exceptionally powerful for natural, ground-level photography, applying it to top-down remote sensing reveals several fundamental disadvantages. Below is the breakdown of these issues and our engineering solutions to mitigate or completely fix them for the DepthWizard prototype.

---

## 1. Shadow Interference (The "Trench" Artifact)
**The Disadvantage:** 
In satellite imagery, tall buildings and trees cast harsh, dark shadows. Because Depth Anything V2 was trained on natural images where dark areas often correlate with background or depth, it frequently misinterprets these shadows as deep holes or "trenches" in the ground.

**The Solution:**
* **Complete Fix (Pre-processing):** Implement an automated **Shadow Detection and Mitigation** pipeline before passing the image to the model. We will convert the image to HSV/LAB color space, isolate the shadow masks, and use histogram equalization (or a fast inpainting algorithm) to artificially lighten the shadows to match the surrounding ground albedo. By stripping the shadow visually, the depth model will correctly predict a flat ground surface.
* **Band-Aid (Post-processing):** Apply a Guided Filter to the output depth map, using the original RGB image as the guide. This forces the depth map edges to align strictly with physical object edges, reducing the shadow bleed.

## 2. Domain Shift (Perspective Misunderstanding)
**The Disadvantage:** 
The model is trained primarily on egocentric (human eye-level) views. In nadir (top-down) satellite imagery, a flat roof can look identical to a flat patch of ground. The model relies heavily on perspective cues (vanishing points, horizon lines) which simply do not exist in orthorectified satellite images.

**The Solution:**
* **Band-Aid (Prototype Scope):** Since we cannot retrain the core foundation weights from scratch within a hackathon timeframe, we will mitigate this by strictly curating our input imagery for the demo to feature **strong geometric contrast** (e.g., modern cities with distinct rooftop textures). Furthermore, we can use an auxiliary building-segmentation model (like a lightweight YOLO or Segment Anything) to mask out buildings, ensuring they are forcefully raised above the ground plane in post-processing.

## 3. Lack of Absolute Metric Scale
**The Disadvantage:** 
Depth Anything V2 outputs *relative* depth (a matrix of values usually normalized between 0 and 1, or 0 and 255). It has no concept of meters or feet. A building could be 10 meters tall or 100 meters tall; the output array looks identical.

**The Solution:**
* **Complete Fix (Our Scale Calibration Module):** We will completely resolve this by building the **Metric Scale Calibration Engine** (as designed in our Requirements document). For any georeferenced image (GeoTIFF), we will automatically download the coarse SRTM 30m DEM for the exact bounding box. We will then perform a robust RANSAC linear regression to map the high-resolution relative depth to the low-resolution metric anchors ($Z_{metric} = s \cdot Z_{relative} + t$). This perfectly converts the scale-agnostic output into a geographically accurate metric DSM.

## 4. Vegetation and Canopy Penetration
**The Disadvantage:** 
Depth Anything V2 will estimate the height of the top of the tree canopy. It cannot "see" the ground underneath a dense forest, unlike LiDAR which can penetrate foliage.

**The Solution:**
* **Intentional Ignorance (Acceptable limitation):** We will **ignore** this limitation. The ISRO problem statement explicitly asks for a **Digital Surface Model (DSM)**, not a Digital Elevation Model (DEM / bare-earth). A DSM *is supposed* to include the height of the tree canopy. Therefore, outputting the canopy top is scientifically correct for our specific requirement.

## 5. Atmospheric Noise and Clouds
**The Disadvantage:** 
Thin cirrus clouds, haze, or smog introduce milky overlays that confuse the depth model, causing it to render clouds as physical floating terrain geometry.

**The Solution:**
* **Band-Aid:** Cloud removal is an entirely separate and complex remote-sensing problem. For this prototype, we will apply a strict operational constraint: **The prototype requires cloud-free imagery (< 5% cloud cover).** We will ensure our curated presentation dataset is entirely cloud-free. 

---

### Summary of Engineering Action Items
To make Depth Anything V2 work flawlessly for the prototype, our pipeline will execute in this order:
1. **Input Image** $\rightarrow$ **Shadow Mitigation Pre-processor** (Fixes Trench Artifacts)
2. **Processed Image** $\rightarrow$ **Depth Anything V2 Inference** (Generates Relative DSM)
3. **Relative DSM** $\rightarrow$ **Edge-Preserving Guided Filter** (Fixes Domain Shift Blur)
4. **Filtered Relative DSM** $\rightarrow$ **SRTM Calibration Engine** (Fixes Absolute Scale)
5. **Output Metric GeoTIFF DSM**
