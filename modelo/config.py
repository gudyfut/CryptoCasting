import torch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
RESULTADOS_DIR = DADOS_DIR / "resultados"

PAR_PRINCIPAL = "BTCUSDT"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

D_INPUT = 39
D_MODEL = 32
N_LAYERS = 2
D_STATE = 16
D_CONV = 4
EXPAND = 2

POOLING = "last"
NUM_CLASSES = 2

BATCH_SIZE = 64
EPOCHS = 100
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 1e-3
DROPOUT = 0.3
EARLY_STOP_PATIENCE = 20
GRAD_CLIP = 1.0

SEED = 42
