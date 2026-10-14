#!/usr/bin/env bash
# =============================================================================
# DepthWizard — One-Command Setup Script
# ISRO Hackathon 2025 | Single-View Height Estimation & 3D Flythrough
# =============================================================================
set -euo pipefail

# --- Colour helpers -----------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  DepthWizard — Environment Setup             ║${RESET}"
echo -e "${BOLD}${CYAN}║  ISRO Hackathon 2025 | SAC Problem #26175    ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${RESET}"
echo ""

# --- Step 1: Verify Python 3.13+ ----------------------------------------------
info "Checking Python version..."

PYTHON_BIN=""
for candidate in python3.14 python3.13 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        major="${version%%.*}"; minor="${version##*.}"
        if [[ "$major" -ge 3 && "$minor" -ge 13 ]]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    error "Python 3.13 or higher is required but not found.\n\
  → Install via your package manager, e.g.:\n\
      Arch Linux:  sudo pacman -S python\n\
      Ubuntu/Deb:  sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.13\n\
      macOS:       brew install python@3.13"
fi

PYTHON_VER=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
success "Python $PYTHON_VER found at $(command -v "$PYTHON_BIN")"

# --- Step 2: Install uv if missing -------------------------------------------
info "Checking for uv package manager..."

if ! command -v uv &>/dev/null; then
    warn "uv not found. Installing via the official installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload PATH to pick up newly installed uv
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    if ! command -v uv &>/dev/null; then
        error "uv installation failed. Please install manually:\n  curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    success "uv installed successfully."
else
    UV_VER=$(uv --version | head -1)
    success "uv found: $UV_VER"
fi

# --- Step 3: Sync dependencies ------------------------------------------------
info "Syncing Python dependencies with uv (this may take a moment on first run)..."
info "Note: PyTorch + transformers are large downloads (~3–5 GB total on first install)."
uv sync
success "All dependencies installed into .venv"

# --- Step 4: Set up .env file -------------------------------------------------
info "Setting up environment configuration..."

if [[ -f ".env" ]]; then
    warn ".env already exists — skipping copy. Edit it manually if needed."
else
    cp .env.example .env
    success ".env created from template. Edit it to add your API keys:"
    echo -e "    ${YELLOW}nano .env${RESET}"
fi

# --- Step 5: Create asset storage directory -----------------------------------
ASSET_DIR="${ASSET_STORAGE_DIR:-/tmp/depthwizard_exports}"
info "Creating asset storage directory at $ASSET_DIR..."
mkdir -p "$ASSET_DIR"
success "Asset directory ready: $ASSET_DIR"

# --- Step 6: Check for model weights (optional) --------------------------------
info "Checking for local model weights..."

LARGE_MODEL="models/depth_anything_v2_large"
SMALL_MODEL="models/depth_anything_v2_small"

if [[ -d "$LARGE_MODEL" && -f "$LARGE_MODEL/model.safetensors" ]]; then
    success "Local LARGE model found at $LARGE_MODEL — will be used preferentially."
elif [[ -d "$SMALL_MODEL" && -f "$SMALL_MODEL/model.safetensors" ]]; then
    success "Local SMALL model found at $SMALL_MODEL — will be used."
else
    warn "No local model weights found in ./models/"
    warn "The server will auto-download Depth Anything V2 Large from HuggingFace Hub on first run."
    warn "To pre-cache the model locally (saves ~1.35 GB), run:"
    echo -e "    ${CYAN}uv run python -c \"from transformers import pipeline; p = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Large-hf'); p.save_pretrained('models/depth_anything_v2_large')\"${RESET}"
fi

# --- Step 7: Check CUDA availability ------------------------------------------
info "Checking GPU/CUDA availability..."
CUDA_STATUS=$(uv run python -c "import torch; print('CUDA available' if torch.cuda.is_available() else 'CPU only')" 2>/dev/null || echo "Could not check (torch not yet imported)")
if [[ "$CUDA_STATUS" == *"CUDA available"* ]]; then
    VRAM=$(uv run python -c "import torch; print(f'{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB VRAM on {torch.cuda.get_device_name(0)}')" 2>/dev/null || echo "Unknown")
    success "GPU detected: $VRAM"
else
    warn "No CUDA GPU detected. DepthWizard will run in CPU-only mode (inference will be slower)."
fi

# --- Done! -------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║  Setup complete! Start DepthWizard with:             ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}uv run uvicorn depth_wizard.api:app --host 0.0.0.0 --port 8000 --reload${RESET}"
echo ""
echo -e "  Then open ${CYAN}http://localhost:8000${RESET} in your browser."
echo ""
echo -e "  Run tests with:  ${YELLOW}uv run pytest -v -s${RESET}"
echo ""
