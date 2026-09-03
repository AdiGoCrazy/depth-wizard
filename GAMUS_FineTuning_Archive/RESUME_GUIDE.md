# Resuming the GAMUS Fine-Tuning Initiative

**Purpose:** This document serves as a "save state" for the DepthWizard project. If we ever decide to move away from the zero-shot Depth Anything V2 + FastSAM architecture and train a domain-native model for satellite imagery, start here.

## 1. What was the plan?
We evaluated the **GAMUS** dataset (a 80GB huggingface remote sensing dataset) and determined it was perfectly suited to solve the "Minecraft Canyon" and "Domain Gap" issues natively. Instead of relying on manual toggles (Urban vs Terrain) and FastSAM to artificially flatten edges, a model trained on GAMUS would natively predict sharp buildings and smooth mountains.

We drafted a comprehensive 4-step execution strategy:
1.  **Environment Isolation:** Provisioning a cloud GPU (e.g., RunPod) and isolating the code so the main prototype doesn't break.
2.  **Data Curation:** Extracting a balanced **10GB stratified sample** (Urban, Hilly, Sparse) instead of downloading all 80GB, to ensure we can train within 48 hours.
3.  **Model Training:** Using **LoRA (Low-Rank Adaptation)** on the Depth Anything V2 ViT encoder to prevent catastrophic forgetting. We mandated a **Scale-Invariant Loss Function** to ensure the depth map remains linear and doesn't break our SRTM RANSAC calibration engine.
4.  **Integration:** Building a parallel `/process_image_v2` A/B testing endpoint to run the models side-by-side.

## 2. Where is the detailed documentation?
All the deep-dive research, risk analyses, and detailed implementation guides generated during this phase have been safely archived in this directory (`/GAMUS_FineTuning_Archive/`). 

Read these files in order when you are ready to resume:
1.  `GAMUS_FEASIBILITY_REPORT.md` (The high-level justification)
2.  `FINE_TUNING_STRATEGY.md` (The core architectural strategy)
3.  `FINETUNING_STEP1_ENVIRONMENT.md` (Cloud GPU & Isolation instructions)
4.  `FINETUNING_STEP2_DATA_CURATION.md` (How to parse the 10GB dataset properly)
5.  `FINETUNING_STEP3_MODEL_TRAINING.md` (LoRA injection and Loss constraints)
6.  `FINETUNING_STEP4_INTEGRATION.md` (Safe A/B integration into the API)

## 3. Immediate Next Steps to Resume
When you wake this project back up:
1. Review the files listed above.
2. Provision a cloud GPU instance with an A100.
3. Write the Python `datasets` ingestion script outlined in Step 2.
4. Begin the LoRA fine-tuning loop outlined in Step 3.
