# GAMUS Dataset: Feasibility & Capability Analysis

This report analyzes the **GAMUS** dataset (provided by Earthflow) and evaluates its potential role, technical feasibility, and the impact it would have if integrated into the DepthWizard project.

---

## 1. Technical Capabilities of the GAMUS Dataset
GAMUS is an open-source dataset specifically built for remote-sensing depth estimation. Based on the requirements provided, its core capabilities include:
*   **Paired Modalities:** It provides direct pairs of **2D top-down optical satellite imagery** and their corresponding **Depth Maps**.
*   **Topographical Diversity:** It includes data spanning varied environments (urban, sparse, hilly, and forested landscapes).
*   **Scale-Agnostic Nature:** The depth data provided is relative (scale-agnostic), meaning it still requires an external anchor for absolute metric scaling.

---

## 2. Role in the DepthWizard Architecture
Currently, DepthWizard relies on **Depth Anything V2** (a model trained heavily on forward-facing, human-perspective images). To make it work for satellites, we had to build a complex, multi-stage "Band-Aid" architecture:
1.  **Pre-processing:** CLAHE & Shadow Enhancement.
2.  **Context-Aware Router:** A manual UI toggle forcing the user to declare if an image is "Urban" or "Terrain".
3.  **FastSAM Segmentation:** Artificially chopping and flattening building edges because the core model blurs them.

**If we train a model on GAMUS, the architecture fundamentally shifts:**
The GAMUS-trained model would replace *both* Depth Anything V2 and FastSAM. Because it is trained natively on nadir (top-down) imagery, it natively understands that building roofs are flat plateaus and mountains are smooth gradients.

---

## 3. Would Training a Model on this Data be Beneficial?
**Yes, immensely beneficial.** Transitioning from a zero-shot foundational model to a domain-specific model trained on GAMUS would elevate DepthWizard from a "clever prototype" to a production-grade remote sensing engine.

### What it would fix for us:
1.  **Elimination of the "Domain Gap":** The model will no longer be confused by top-down perspectives. Building roofs will naturally separate from the ground without bleeding edges.
2.  **Removal of the "Minecraft Canyon" Effect:** We will no longer need the FastSAM segmentation step. The model will naturally predict sharp structural drops for buildings and smooth, continuous slopes for terrain in a single inference pass.
3.  **Deprecation of the Context-Aware Toggle:** The system will become fully autonomous. Users will no longer have to manually select "Urban" or "Terrain" because the model will inherently understand both structural variations.
4.  **Massive Performance Boost:** By stripping out FastSAM and complex pre-processing, inference time and VRAM requirements will plummet, making the system much faster and cheaper to run.

---

## 4. Feasibility & Integration Strategy
**Feasibility: High, but requires a strategic pivot.**
*   **Training Infrastructure:** We would need to pivot from purely running inference to establishing a PyTorch training pipeline. We can use the open-source `RSI-MMSegmentation` dataloader linked in the Hugging Face repository to streamline data ingestion.
*   **Model Selection:** We could either fine-tune our existing Depth Anything V2 backbone using GAMUS (Transfer Learning) or train a lighter-weight CNN/Transformer (like MiDaS or a Swin Transformer) from scratch on this data.
*   **What Stays the Same (Calibration):** Because GAMUS provides scale-agnostic depth, our **Phase 5: Metric Scale Calibration** using RANSAC Regression and the SRTM 30m DEM anchor remains **100% vital and unchanged**. The GAMUS model will predict the relative shapes perfectly, and our existing calibration engine will give those shapes absolute metric height.

## Conclusion
Adopting the GAMUS dataset solves the root cause of every major bug we faced during development. Instead of patching a forward-facing AI with FastSAM and UI toggles, GAMUS allows us to train an AI that natively speaks the language of satellite imagery.
