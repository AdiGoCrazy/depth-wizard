# Fine-Tuning Step 1: Environment Isolation & Provisioning

This document provides a highly detailed plan for isolating the fine-tuning workflow from the live DepthWizard prototype and provisioning the necessary compute resources.

---

## 1. Detailed Implementation Plan

The goal of this step is to ensure that the rigorous and unstable process of training a machine learning model does not pollute, crash, or alter the `master` branch of our working prototype.

**Actionable Steps:**
1.  **Git Branching Strategy:** We will create a new isolated git branch specifically for training: `git checkout -b feature/gamus-finetuning`.
2.  **API Separation:** Inside the codebase, the original `DepthAnythingV2` inference class in `src/depth_wizard/api.py` will remain completely untouched. We will create a duplicated, separate class named `DepthAnythingSatelliteTrainer`. This ensures that even if we accidentally push broken code, the web UI and standard API endpoints will continue to call the stable, zero-shot model.
3.  **Compute Provisioning:** We will rent a dedicated cloud GPU instance. Our stack requires Linux (Ubuntu 22.04), CUDA 12.1+, and Python 3.13. We will initialize the server using a Docker container specifically configured for PyTorch `2.2.0` to avoid dependency conflicts on the local host.
4.  **Data Volume Mounting:** We will attach an external NVMe block storage volume (at least 250GB) to the cloud instance to hold the raw 80GB GAMUS dataset, the extracted subsets, and the massive optimizer states during training.

---

## 2. Advantages and Disadvantages of Provisioning Methods

To acquire the necessary GPU compute, there are three distinct paths.

### Option A: Local Compute (Consumer GPUs)
Attempting to train on local hardware (e.g., a single RTX 3090/4090).
*   **Advantages:** Free (no hourly rental costs), complete data privacy, no network bottleneck for uploading data.
*   **Disadvantages:** VRAM constraints (24GB max) heavily limit batch sizes and require massive gradient accumulation. A single epoch could take days, meaning a 48-hour deadline is impossible. Overheats local machines.

### Option B: Managed ML Services (AWS SageMaker / GCP Vertex)
Using enterprise managed infrastructure designed for ML pipelines.
*   **Advantages:** Highly robust, automatic scaling, built-in experiment tracking (TensorBoard integration), and zero terminal/sysadmin setup required.
*   **Disadvantages:** Extremely expensive. The abstraction layers make it very difficult to debug low-level CUDA OOM (Out of Memory) errors quickly. Steep learning curve for configuration.

### Option C: Bare-Metal Cloud GPUs (RunPod / Lambda Labs) - *[Recommended]*
Renting unmanaged bare-metal instances (e.g., 1x A100 80GB or 4x RTX 4090).
*   **Advantages:** Extremely cost-effective ($1-$2/hour), full root SSH access for instantaneous debugging, massive VRAM allows for larger batch sizes (faster convergence).
*   **Disadvantages:** Requires manual setup of Docker, CUDA drivers, and SSH tunnels. If the instance crashes, you must manually rescue the data.

---

## 3. Risk Analysis & Mitigation

### Risk 1.1: Dependency Pollution
*   **The Risk:** Fine-tuning requires libraries like `peft`, `accelerate`, and `bitsandbytes` which can overwrite or conflict with the strict dependency versions required by our FastSAM segmentation engine. If this happens, the entire prototype breaks.
*   **Mitigation Strategy:** Strict isolation using Python `uv` virtual environments (`.venv-train`) and Docker containers. The training environment will never share a `requirements.txt` with the production backend.

### Risk 1.2: Cloud Instance Ephemerality
*   **The Risk:** Cloud GPU instances are often preemptible or can crash due to hardware faults. If the instance dies 20 hours into a 24-hour training run, all progress and downloaded data (80GB) is instantly destroyed.
*   **Mitigation Strategy:** 
    1.  Always use attached, persistent NVMe volumes rather than the instance's boot drive. 
    2.  Implement aggressive checkpointing in PyTorch, saving the model weights and the AdamW optimizer state to the persistent volume every 500 steps. If the machine dies, we can resume training from the exact step without losing more than a few minutes of progress.
