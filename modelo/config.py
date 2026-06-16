import torch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"
RESULTADOS_DIR = DADOS_DIR / "resultados"

PAR_PRINCIPAL = "BTCUSDT"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

D_INPUT = 15
D_MODEL = 64
N_LAYERS = 4
D_STATE = 16
D_CONV = 4
EXPAND = 2

POOLING = "last"
NUM_CLASSES = 2

BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
DROPOUT = 0.1
EARLY_STOP_PATIENCE = 10
GRAD_CLIP = 1.0

SEED = 42
