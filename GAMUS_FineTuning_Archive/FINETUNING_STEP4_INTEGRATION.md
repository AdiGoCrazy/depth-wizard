# Fine-Tuning Step 4: Export & Integration

This document outlines the strategy for safely exporting the newly fine-tuned model weights and seamlessly integrating them back into the DepthWizard pipeline without breaking the existing stable prototype.

---

## 1. Detailed Implementation Plan

The objective is to replace our current "Band-Aid" architecture (FastSAM + Context-Aware Routing) with the newly trained, domain-native model in a highly controlled, A/B testing environment.

**Actionable Steps:**
1.  **Weight Consolidation:** Once the LoRA training loop finishes on the cloud instance, the LoRA adapters (the tiny trained matrices) are computationally merged back into the frozen base model weights. This creates a single, standalone PyTorch `.safetensors` file.
2.  **Export & Download:** The `.safetensors` file and the updated model config are downloaded from the cloud GPU back to our local testing environment and placed into a new `src/depth_wizard/models/` directory.
3.  **Pipeline Integration:** In `src/depth_wizard/api.py`, we instantiate the new `DepthAnythingSatellite` class pointing to the local `.safetensors` file.
4.  **A/B Testing Endpoints:** We create a secondary API endpoint (`/process_image_v2`) that routes directly to the new model. The original `/process_image` endpoint remains untouched, allowing us to simultaneously process the exact same image through both the old system and the new system to compare accuracy.
5.  **Deprecation of Band-Aids:** If the new model proves superior, we will systematically delete the FastSAM module, the Pre-processing module, and the UI Context Toggle.

---

## 2. Advantages and Disadvantages of Integration Methods

### Option A: Direct Replacement (In-Place Overwrite)
Immediately swapping out the old `DepthAnythingV2` weights for the new weights and deleting FastSAM.
*   **Advantages:** Extremely fast. Cleans up the codebase instantly.
*   **Disadvantages:** High risk. If the new model fails on a specific edge case during the final hackathon presentation, we have no fallback. We have effectively destroyed a working prototype.

### Option B: A/B Parallel Integration - *[Recommended]*
Running both the old system and the new system simultaneously via different API endpoints until the new system is proven perfectly stable.
*   **Advantages:** Zero risk to the existing presentation prototype. Allows for direct, side-by-side visual comparison of the "Band-Aid" fix vs. the Native Machine Learning fix.
*   **Disadvantages:** Requires holding two massive AI models in VRAM simultaneously during testing, which may cause local Out-Of-Memory (OOM) crashes unless we test them sequentially.

---

## 3. Risk Analysis & Mitigation

### Risk 4.1: VRAM Exhaustion During Integration
*   **The Risk:** If we attempt to load both the original Depth Anything V2 model (for the old pipeline) and the new GAMUS-trained model (for the new pipeline) into a single 4GB or 8GB GPU to run an A/B test, PyTorch will immediately throw a CUDA OOM crash.
*   **Mitigation Strategy:** We will strictly implement synchronous execution during A/B testing. The API will load the old model, run inference, flush the GPU memory (`torch.cuda.empty_cache()`), and *then* load the new model into VRAM to run the second inference.

### Risk 4.2: Inference Latency Spikes
*   **The Risk:** Sometimes merged LoRA models or updated configurations can inadvertently disable `torch.compile` or FlashAttention optimizations, resulting in the new model running significantly slower than the original zero-shot model.
*   **Mitigation Strategy:** Post-training optimization. Before finalizing the integration, we will explicitly re-run `torch.compile(mode="reduce-overhead")` on the new `DepthAnythingSatellite` class and profile the inference time against the original model. If the new model is slower despite lacking the FastSAM overhead, we will investigate the attention block configurations in the exported weights.
