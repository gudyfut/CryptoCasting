import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json
from qualificacao.dados_sinteticos import dados_artificiais
from experimentos.walkforward_diario.dados import configuracao_bloco, preparar


class DadosWalkForward(unittest.TestCase):
    def test_blocos_janelas_escala_e_perturbacao_futura(self):
        base=ler_json(RAIZ/'dados/experimentos/fechamento_ramos_diarios_18efadab3f5a3771aacd/BTCUSDT/configuracao.json')
        cfg=ler_json(RAIZ/'configuracoes/walkforward_diario_001.json')
        df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
        for b in cfg['blocos']:
            c=configuracao_bloco(base,b,cfg['treino_inicio'])
            d,e=preparar(df,c)
            origem=d['teste']['origens_ms'][0]
            alterado=df.copy();alterado.loc[alterado.open_time>=origem,['open','high','low','close','volume']]*=1.2
            d2,e2=preparar(alterado,c)
            self.assertEqual(e,e2)
            np.testing.assert_array_equal(d['teste']['x'][0],d2['teste']['x'][0])
            self.assertNotEqual(d['teste']['y'][0],d2['teste']['y'][0])
            np.testing.assert_array_equal(d['validacao']['x'],d2['validacao']['x'])


if __name__=='__main__':unittest.main()
