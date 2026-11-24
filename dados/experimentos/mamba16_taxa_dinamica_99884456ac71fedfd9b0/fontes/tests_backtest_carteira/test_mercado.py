import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from backtest_carteira.mercado import carregar


class Mercado(unittest.TestCase):
    def test_matriz_propria_e_preservacao_da_origem(self):
        q=pd.DataFrame({'inicio_utc':pd.date_range('2025-01-01',periods=3,freq='min',tz='UTC'),**{k:[100.,100.,100.] for k in ('open','high','low','close','volume','negocios')},'completo':[True,False,True]})
        antes=q.copy(deep=True);ct={'configuracao':{'mercado_pasta':'fixture'},'mercado_partes':[{'arquivo':'a.parquet','periodo':{'inicio':'2025-01-01'}}]}
        with patch('backtest_carteira.mercado.pd.read_parquet',return_value=q):m,primeiro=carregar(None,ct)
        self.assertTrue(m.flags.writeable);self.assertTrue(np.isnan(m[1]).all());pd.testing.assert_frame_equal(q,antes);self.assertEqual(primeiro,int(pd.Timestamp('2025-01-01T00:00Z').timestamp()//60))

    def test_recusa_lacuna_em_vez_de_interpolar(self):
        q=pd.DataFrame({'inicio_utc':pd.to_datetime(['2025-01-01T00:00Z','2025-01-01T00:02Z'])})
        ct={'configuracao':{'mercado_pasta':'fixture'},'mercado_partes':[{'arquivo':'a','periodo':{'inicio':'2025'}}]}
        with patch('backtest_carteira.mercado.pd.read_parquet',return_value=q),self.assertRaises(ValueError):carregar(None,ct)
