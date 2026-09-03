# Fine-Tuning Step 3: Model Configuration & Training Loop

This document details the exact machine learning architecture and training loop configurations required to successfully fine-tune the Depth Anything V2 model.

---

## 1. Detailed Implementation Plan

The goal is to modify the internal weights of the model so it naturally learns top-down geometry without destroying its foundational understanding of depth physics.

**Actionable Steps:**
1.  **Architecture Initialization:** We load the `DepthAnythingV2` Hugging Face model (`Large` variant, approximately ~1.3B parameters).
2.  **PEFT Injection:** Using the `peft` library, we inject LoRA (Low-Rank Adaptation) matrices into the Query (Q) and Value (V) projection layers of the Vision Transformer (ViT) encoder blocks.
3.  **Loss Function Design:** We will define a composite loss function:
    *   **Scale-Invariant Loss:** Ensures the relative depth relationship is maintained.
    *   **Gradient Matching Loss:** Penalizes the model heavily if its predicted depth map does not have sharp edges where the ground truth depth map has sharp edges (forcing crisp buildings).
4.  **Training Loop:** We utilize the AdamW optimizer with a very conservative learning rate (e.g., `1e-5`) and a Cosine Annealing learning rate scheduler with warmup. 
5.  **Validation:** After every 10% of an epoch, the model is evaluated against a strict held-out validation set of GAMUS images. If the validation loss stagnates, early stopping is triggered.

---

## 2. Advantages and Disadvantages of Fine-Tuning Architectures

### Option A: Full Fine-Tuning (End-to-End)
Unfreezing every single parameter in the 1.3 Billion parameter model.
*   **Advantages:** Theoretically achieves the absolute highest possible accuracy on the GAMUS dataset because the entire network adapts to the remote sensing domain.
*   **Disadvantages:** VRAM prohibitive. Updating 1.3B parameters + storing optimizer states requires ~80GB-100GB of VRAM just to process a single batch. Training is extremely slow. Extremely high risk of catastrophic forgetting.

### Option B: Freezing the ViT Encoder, Training the DPT Decoder
Locking the massive vision transformer (which extracts general image features) and only training the smaller DPT decoder heads (which translate features into a depth map).
*   **Advantages:** Massive VRAM savings. Extremely fast training loops.
*   **Disadvantages:** The ViT encoder was trained on forward-facing photos. If it fundamentally fails to extract structural features from top-down satellite imagery, the decoder cannot magically create them. The performance ceiling is relatively low.

### Option C: LoRA (Low-Rank Adaptation) - *[Recommended]*
Freezing the original network but injecting tiny, trainable matrices into the attention layers.
*   **Advantages:** It updates less than 1% of the total model parameters, meaning it trains lightning fast and uses minimal VRAM (can easily run on a 24GB consumer GPU if needed). Because the core weights are frozen, it physically cannot suffer from catastrophic forgetting, retaining its foundational zero-shot robustness while learning the specific "flavor" of satellite imagery.
*   **Disadvantages:** Slightly more complex to code (requires PEFT library integration). May require tuning the LoRA rank parameter ($r$) and alpha.

---

## 3. Risk Analysis & Mitigation

### Risk 3.1: "Catastrophic Forgetting"
*   **The Risk:** The model memorizes the specific texture of GAMUS satellite imagery and forgets how to calculate depth entirely. If fed an image with a different color grade, it outputs static noise.
*   **Mitigation Strategy:** LoRA inherently prevents the most severe forms of catastrophic forgetting because the foundational weights are frozen. To be extra safe, we will implement strict **Early Stopping**. If the validation loss increases over 3 consecutive evaluations, training stops instantly to prevent overfitting.

### Risk 3.2: Calibration Disconnect (Non-Linearity)
*   **The Risk:** GAMUS provides relative depth. DepthWizard relies on RANSAC regression against SRTM 30m to generate absolute metric height. If our training loss function allows the model to predict depth on an exponential scale (e.g., predicting mountains as $x^2$ taller than buildings), our linear calibration equation ($Z = s \cdot Z_{rel} + t$) will fail entirely.
*   **Mitigation Strategy:** We must mathematically enforce linearity during training. By relying heavily on **Scale-Invariant Signal-to-Noise Ratio (SI-SNR)** as the primary loss metric, we punish the model if the relationship between two pixels is non-linear compared to the ground truth. This guarantees the output remains perfectly compatible with our Phase 5 Calibration Engine.
