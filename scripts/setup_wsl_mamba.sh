#!/bin/bash
set -ex
export TMPDIR=$HOME/.tmp
mkdir -p $TMPDIR

source $HOME/.venvs/cc/bin/activate

echo "=== Step 1: Reinstall PyTorch 2.6.0 + CUDA 11.8 ==="
pip uninstall torch -y
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118

echo "=== Step 2: Install causal-conv1d (GitHub wheel) ==="
pip install --no-deps "https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.6.2.post1/causal_conv1d-1.6.2.post1%2Bcu11torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl"

echo "=== Step 3: Install mamba-ssm (GitHub wheel) ==="
pip install --no-deps "https://github.com/state-spaces/mamba/releases/download/v2.3.2.post1/mamba_ssm-2.3.2.post1%2Bcu11torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl"

echo "=== Step 4: Install Python deps ==="
pip install einops packaging ninja transformers

echo "=== Step 4b: Patch mamba-ssm __init__.py (Mamba3 needs triton 3.5+)"
INIT_PY="$VIRTUAL_ENV/lib/python3.12/site-packages/mamba_ssm/__init__.py"
if grep -q "from mamba_ssm.modules.mamba3 import Mamba3" "$INIT_PY"; then
    sed -i 's/^from mamba_ssm.modules.mamba3 import Mamba3/try:\n    from mamba_ssm.modules.mamba3 import Mamba3\nexcept Exception:\n    pass/' "$INIT_PY"
    echo "Patched."
fi

echo "=== Step 5: Install project requirements ==="
projeto_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$projeto_dir"
pip install -r requirements.txt

echo "=== Step 6: Verify ==="
python -c "import torch; print(f'torch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
python -c "from mamba_ssm import Mamba; print('mamba-ssm: OK')" 2>&1 || echo "WARNING: mamba-ssm import failed - project will use fallback"
