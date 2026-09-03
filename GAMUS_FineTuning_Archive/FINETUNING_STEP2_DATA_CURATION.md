# Fine-Tuning Step 2: GAMUS Data Curation

This document expands on the strategy for downloading, slicing, and structuring the GAMUS dataset to guarantee efficient and robust training within a strict 48-hour deadline.

---

## 1. Detailed Implementation Plan

The objective is to avoid training on the entire 80GB dataset, which is mathematically impossible within 2 days, and instead create a highly potent 10GB subset.

**Actionable Steps:**
1.  **Scripted Ingestion:** We will write a Python script using the `datasets` library from Hugging Face to stream the dataset metadata without downloading all 80GB initially.
2.  **Stratified Sampling:** We will algorithmically sort the dataset based on its provided metadata tags to extract exactly 3.3GB of Urban scenes, 3.3GB of Hilly/Terrain scenes, and 3.3GB of Sparse/Forested scenes.
3.  **Dataloader Construction:** We will adapt the `RSI-MMSegmentation` dataloader logic. The dataloader must return a tuple: `(RGB_Image_Tensor, Depth_Map_Tensor)`.
4.  **Data Augmentation Pipeline:** Using `torchvision.transforms`, we will build an augmentation pipeline that runs *live* during training. This pipeline will randomly flip images horizontally, apply slight color jitter (brightness, contrast, hue), and randomly crop patches from the high-resolution satellite tiles to match the input resolution expected by the Vision Transformer (e.g., $518 \times 518$).

---

## 2. Advantages and Disadvantages of Curation Methods

### Option A: Train on the Full 80GB
*   **Advantages:** Maximizes the model's exposure to every possible geographic edge case. Eliminates sampling bias.
*   **Disadvantages:** I/O bottleneck. Downloading and parsing 80GB takes significant time. Training takes an exponentially longer time per epoch. Completely unviable for a fast hackathon prototype.

### Option B: Random 10GB Slice (Unstratified)
*   **Advantages:** Extremely fast to implement. Just grab the first 10GB of the parquet files and start training immediately.
*   **Disadvantages:** High risk of geographic bias. If the first 10GB happens to be entirely dense urban cities, the model will fail on natural terrain (re-introducing the exact "Minecraft Canyon" bug we are trying to fix).

### Option C: Stratified 10GB Slice - *[Recommended]*
*   **Advantages:** Balances the dataset perfectly. Ensures the model learns sharp urban edges alongside smooth mountain gradients equally. Maximizes the "learning density" of the data.
*   **Disadvantages:** Requires custom Python scripting to parse metadata and organize the files into explicit folders before training begins, costing 1-2 hours of engineering time upfront.

---

## 3. Risk Analysis & Mitigation

### Risk 2.1: The "Shadow Bias" Trap
*   **The Risk:** GAMUS optical images contain natural shadows cast by buildings and mountains. If we don't augment the data, the AI is notoriously lazy; it will simply learn that "shadow = steep drop" instead of actually analyzing the geometry. When fed an image taken at solar noon (no shadows), it will predict flat terrain.
*   **Mitigation Strategy:** Aggressive photometric augmentation. By artificially jittering the brightness and contrast of the RGB tensor *without* altering the Depth tensor, we force the model to rely on structural features rather than relying on shadow presence.

### Risk 2.2: Resolution & GSD (Ground Sample Distance) Mismatch
*   **The Risk:** GAMUS images are provided at a specific resolution. If we train the model to recognize a house that is exactly $50 \times 50$ pixels wide, it will fail in production if a user uploads a zoomed-out image where a house is only $5 \times 5$ pixels wide.
*   **Mitigation Strategy:** Scale Jittering. During the Dataloader step, we must implement random resize cropping (e.g., zooming in 2x or zooming out 0.5x) before passing the tensor to the model. This guarantees the model learns to identify depth shapes regardless of their pixel scale, keeping it truly zero-shot across different satellite providers.
