import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from barreiras.treino import treinar
from barreiras.ar1 import probabilidades


@unittest.skipUnless(torch.cuda.is_available(),'Qualificação dos kernels exige CUDA.')
class ModelosTest(unittest.TestCase):
    def test_prefixos_e_bancos_monte_carlo(self):
        a={'intercepto':0.,'phi':.1,'sigma_residual':.003}
        um=probabilidades(a,.001,.003,[1],42)
        dois=probabilidades(a,.001,.003,[1,2],42)
        np.testing.assert_array_equal(um,dois[:1])
        banco2=probabilidades(a,.001,.003,[1],43)
        maior=probabilidades(a,.001,.003,[1],42,trajetorias=8192)
        esperado=((um*(4096+1.5)-.5)+(banco2*(4096+1.5)-.5)+.5)/(8192+1.5)
        np.testing.assert_allclose(maior,esperado,rtol=0,atol=1e-15)

    def test_treino_recarga_e_invariancia_ao_rotulo_de_teste(self):
        raiz=Path(__file__).resolve().parents[1]
        c=json.loads((raiz/'configuracoes/ciclo_001.json').read_text())
        c['treino']['epocas']=2
        c['treino']['paciencia']=2
        rng=np.random.default_rng(19)
        matriz=rng.normal(size=(100,5)).astype(np.float32)
        datas=pd.date_range('2023-01-01',periods=60,freq='h',tz='UTC')
        q=pd.DataFrame({'indice_hora':np.arange(24,84),'distancia':np.full(60,.02),
                        'classe':np.arange(60)%3,'ambiguo':False,'origem_utc':datas})
        blocos={'treino':q.iloc[:32].reset_index(drop=True),'validacao':q.iloc[32:44].reset_index(drop=True),
                'teste':q.iloc[44:].reset_index(drop=True),'operacional':q.iloc[44:].reset_index(drop=True)}
        escalas={'media_aux':np.log(.02),'escala_aux':1.}
        celula={'par':'BTCUSDT','contexto':24,'horizonte':24,'fold':'DB1','seed':42}
        with tempfile.TemporaryDirectory() as pasta:
            for nome in ('lstm','mamba'):
                a=Path(pasta)/nome/'a'
                r,previsoes=treinar(nome,c,celula,matriz,blocos,escalas,a)
                self.assertTrue(r['recarga_exata'])
                self.assertEqual(len(previsoes['teste']),16)
                b=Path(pasta)/nome/'b'
                alterados=copy.deepcopy(blocos)
                alterados['teste']['classe']=(alterados['teste']['classe']+1)%3
                treinar(nome,c,celula,matriz,alterados,escalas,b)
                pa=torch.load(a/'checkpoint.pt',map_location='cpu',weights_only=True)
                pb=torch.load(b/'checkpoint.pt',map_location='cpu',weights_only=True)
                self.assertEqual(pa['epoca'],pb['epoca'])
                for chave in pa['pesos']:
                    # Reduções dos kernels externos podem variar em poucos ULPs
                    # entre treinos; recarga das mesmas previsões continua exata.
                    torch.testing.assert_close(pa['pesos'][chave],pb['pesos'][chave],
                        rtol=0,atol=8*torch.finfo(torch.float32).eps)


if __name__=='__main__':
    unittest.main()
