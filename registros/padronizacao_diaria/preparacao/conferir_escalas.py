import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
ptr=ler_json(RAIZ/'registros/retomada_alvo_diario/execucao.json');f=ler_json(RAIZ/ptr['pasta']/'congelamento.json')
c=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')
d,e=preparar_com_escalas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
r={'escalas':e,'matrizes':{fase:{'forma':list(v['x'].shape),'sha256':hashlib.sha256(v['x'].tobytes()).hexdigest(),'finito':bool(np.isfinite(v['x']).all())} for fase,v in d.items()},'fonte_sha256':sha256(__file__)}
salvar_json(RAIZ/'registros/padronizacao_diaria/preparacao'/('escalas_'+sys.argv[1]+'.json'),r)
print(sys.argv[1],e['candles_unicos'],r['matrizes'])
