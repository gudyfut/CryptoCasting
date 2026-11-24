import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import numpy as np
import pandas as pd
from mercado_futuros.periodo_publico_verificado import completar


class Complementacao(TestCase):
    def test_dia_ausente_recuperado_apenas_por_observacoes_api(self):
        inicio=1782691200000
        esperado=np.arange(inicio,inicio+2*86400000,60000)
        q=pd.DataFrame({'open_time':esperado[1440:], 'close':np.full(1440,100.)})
        extra=pd.DataFrame({'open_time':esperado[:1440], 'close':np.full(1440,101.)})
        with tempfile.TemporaryDirectory() as pasta, patch('mercado_futuros.periodo_publico_verificado.api',return_value=(extra,[{'url':'oficial'}])) as consulta:
            completo,fontes=completar(q,Path(pasta),'BTCUSDT','markPriceKlines','1m',inicio,inicio+2*86400000)
            np.testing.assert_array_equal(completo.open_time,esperado)
            np.testing.assert_array_equal(completo.close,np.r_[np.full(1440,101.),np.full(1440,100.)])
            self.assertEqual(consulta.call_count,1)
            self.assertEqual(fontes[0]['minutos_ou_dias_ausentes_no_trecho'],1440)
