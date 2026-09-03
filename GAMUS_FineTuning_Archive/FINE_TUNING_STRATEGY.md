# Depth Anything V2: Fine-Tuning Strategy & Risk Analysis

This document outlines the comprehensive strategy for fine-tuning the **Depth Anything V2** foundational model on the **GAMUS** remote sensing dataset. The objective is to produce a domain-specific model capable of estimating depth natively from top-down satellite imagery across urban, hilly, and sparse terrains, eliminating the need for our current "Band-Aid" pre-processing and FastSAM segmentation steps. 

Importantly, this fine-tuning effort will occur in an **isolated environment**, leaving the current zero-shot Context-Aware production system entirely untouched.

---

## 1. End-to-End Fine-Tuning Workflow

To achieve a production-ready fine-tuned model without breaking our existing prototype, we will execute the following pipeline:

### Step 1: Environment Isolation
1. **Fork the Pipeline:** We will duplicate the `DepthAnythingV2` class in our backend into a new class (e.g., `DepthAnythingSatellite`). The original API will remain unchanged.
2. **Cloud GPU Provisioning:** Fine-tuning cannot happen locally. We will provision a cloud instance (e.g., RunPod or AWS EC2) with at least 1x NVIDIA A100 (80GB VRAM) or multiple RTX 4090s.

### Step 2: GAMUS Data Curation (The 10GB Slice)
Training on the full 80GB GAMUS dataset is computationally restrictive and unnecessary for a prototype. We will extract a highly curated **10GB stratified sample**.
*   **Balancing:** 3.3GB Urban (dense structures), 3.3GB Hilly (smooth natural slopes), 3.3GB Sparse/Forested.
*   **Normalization:** We will write a custom PyTorch `Dataset` class using the `RSI-MMSegmentation` dataloader logic to normalize the GeoTIFFs into standard tensors, ensuring the 2D optical images perfectly align pixel-for-pixel with the scale-agnostic GAMUS depth maps.

### Step 3: Model Configuration & Fine-Tuning
1. **Load Pre-Trained Weights:** We initialize Depth Anything V2 with its standard weights.
2. **Apply PEFT (Parameter-Efficient Fine-Tuning):** Instead of updating all 300M+ parameters, we will inject LoRA (Low-Rank Adaptation) modules.
3. **Training Loop:** We train using a custom loss function combining **Scale-Invariant Signal-to-Noise Ratio (SI-SNR)** and **Gradient Matching Loss** (to force the model to learn sharp building edges).
4. **Validation:** We validate against a held-out slice of the GAMUS dataset after every epoch.

### Step 4: Export & Integration
Once convergence is reached, the updated weights will be exported as a `.safetensors` file and loaded into the isolated `DepthAnythingSatellite` class for direct side-by-side A/B testing against the old system.

---

## 2. Evaluation of Fine-Tuning Methods

Depth Anything V2 uses a massive Vision Transformer (ViT) encoder and a Dense Prediction Transformer (DPT) decoder. How we fine-tune it is critical.

| Method | Description | Verdict |
| :--- | :--- | :--- |
| **Full Fine-Tuning** | Unfreezing all layers (Encoder + Decoder) and updating every weight in the network. | **REJECTED.** Requires massive VRAM, takes weeks on 80GB of data, and suffers from "Catastrophic Forgetting" (the model forgets general depth rules and wildly overfits to GAMUS). |
| **Frozen Encoder, Train Decoder** | Freezing the massive ViT backbone and only training the DPT decoder heads. | **VIABLE.** Very fast to train and retains the robust feature extraction of the foundational model. However, it may struggle to learn *entirely* new edge-detection rules for top-down buildings. |
| **LoRA (Low-Rank Adaptation)** | Injecting tiny, trainable rank-decomposition matrices into the frozen ViT Attention blocks and the Decoder. | **RECOMMENDED.** The absolute best approach. It trains 100x faster, requires a fraction of the VRAM, and achieves >95% the accuracy of full fine-tuning. It allows the model to deeply learn satellite perspectives without forgetting its foundational knowledge. |

---

## 3. System Advantages & Disadvantages

If we successfully implement this fine-tuned model, how does it compare to our current "Band-Aid" system?

### Advantages (The "Holy Grail")
*   **Native Domain Understanding:** The model inherently understands that top-down buildings have sharp, 90-degree drops and mountains have smooth gradients.
*   **Radical Pipeline Simplification:** We completely delete the `FastSAM` module, the Shadow Enhancement pre-processor, and the `Context-Aware Router`. 
*   **Lower Latency & Memory:** Without running a massive FastSAM segmentation engine alongside the depth model, inference speed drops from seconds to milliseconds, and VRAM requirements are cut in half.
*   **Autonomous Operation:** The user no longer needs to toggle "Urban" or "Terrain". The model handles all geometries seamlessly in one pass.

### Disadvantages
*   **High Upfront Cost:** Requires expensive cloud GPU rental and intense developer hours for MLOps and hyperparameter tuning.
*   **Loss of Absolute Zero-Shot:** The model becomes highly specialized to satellite data. If a user uploads a drone image shot at a 45-degree angle (oblique), the fine-tuned model might fail, whereas the current zero-shot model would likely survive.

---

## 4. In-Depth Risk Analysis & Failure Vectors

Fine-tuning a foundational vision model on geospatial data is notoriously brittle. Here is a deep dive into exactly how and why this system could fail.

### Risk A: "Catastrophic Forgetting" & Overfitting
If we train the model too aggressively (high learning rate or too many epochs), it will forget the generalized depth physics it learned from 60 million real-world images. 
*   *How it fails:* It starts memorizing the GAMUS dataset. If a user uploads a satellite image of a city that looks texturally different than the GAMUS training data, the depth map will dissolve into random noise.
*   *Mitigation:* Use LoRA with a very low rank ($r=8$) and strict early stopping.

### Risk B: The "Shadow Bias" Trap
Optical remote sensing data is heavily influenced by the sun angle at the time the satellite took the photo. 
*   *How it fails:* If the GAMUS dataset has a high concentration of images taken at 3:00 PM (casting long shadows), the model might secretly learn that "dark black pixels = sharp depth drop" instead of actually learning structural geometry. If we then feed it an image taken at noon (no shadows), it will predict the city is completely flat.
*   *Mitigation:* Aggressive Data Augmentation during training (randomly shifting brightness, contrast, and applying artificial shadow masks to the 2D inputs) so the model is forced to ignore shadows.

### Risk C: Resolution & GSD Mismatch
The GAMUS dataset provides images at a specific Ground Sample Distance (e.g., 0.5 meters per pixel). 
*   *How it fails:* The ViT encoder uses fixed-size patch embeddings. If we train the model exclusively on 0.5m GSD images, and then during a live demo we feed it a 30m GSD Landsat image, the physical scale of a "building" in pixels will be radically different. The model will fail to recognize structures.
*   *Mitigation:* Scale Jittering. During training, we must randomly crop, zoom, and resize the GAMUS image tensors before feeding them to the model, ensuring it learns scale-invariant geometry.

### Risk D: Calibration Disconnect
GAMUS provides *relative* depth maps. Our system relies on RANSAC regression against SRTM 30m anchors to generate *absolute* metric height.
*   *How it fails:* If the fine-tuned model outputs relative depth that is highly non-linear (e.g., it exponentially compresses mountain heights), our linear RANSAC equation ($Z = s \cdot Z_{rel} + t$) will fail to calibrate the scale, resulting in floating cities or sunken terrain.
*   *Mitigation:* We must use a **Scale- and Shift-Invariant Loss** function during training. This forces the model's raw output to remain strictly linear to the ground truth, ensuring our RANSAC calibration engine continues to work flawlessly.
