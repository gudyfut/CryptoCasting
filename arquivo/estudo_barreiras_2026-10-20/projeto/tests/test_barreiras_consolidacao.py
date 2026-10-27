import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd

from barreiras.arquivos import salvar_json,sha256,identidade
from barreiras.configuracao import FOLDS,celulas
from barreiras.metricas import calcular
from barreiras.consolidacao import consolidar


class ConsolidacaoTest(unittest.TestCase):
    def test_grade_pareada_sem_ganho_e_integridade(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz=Path(temporario)/'execucoes';raiz.mkdir()
            c={'pares':['BTCUSDT'],'contextos':[24,168],'horizontes':[24],'folds':['DB1','DB2'],'seeds':[42]}
            salvar_json(raiz/'ciclo.json',{'id':'sintetico','assinatura':{'configuracao':c,'dataset':'sintetico','codigo':{}}})
            for i,celula in enumerate(celulas(c)):
                pasta=raiz/str(i);pasta.mkdir()
                limites=FOLDS[celula['fold']].limites()
                datas=pd.date_range(limites[2],limites[3],freq='D',inclusive='left')
                q=pd.DataFrame({'origem_utc':datas,'classe':np.arange(len(datas))%3,'p0':.2,'p1':.3,'p2':.5})
                m=calcular(q.classe,q[['p0','p1','p2']].to_numpy())
                resultados={};financeiro={}
                for nome in ('mamba','lstm','ar1'):
                    p=pasta/nome;p.mkdir();q.to_parquet(p/'previsoes_teste.parquet',index=False)
                    resultados[nome]={'metricas':{'teste':m}}
                    financeiro[nome]={}
                    for variante in ('base','custos_agravados','ambiguidade_superior','sem_filtro'):
                        curva=pd.DataFrame({'minuto_utc':datas.as_unit('s').astype('int64')//60,
                             'patrimonio':10000.,'pior_marca_observavel':10000.,'exposto':False})
                        curva.to_parquet(p/f'curva_{variante}.parquet',index=False)
                        financeiro[nome][variante]={'status':'auditavel','retorno_liquido':0.,'drawdown_maximo':0.}
                    financeiro[nome]['comprar_manter']={'status':'auditavel','retorno_liquido':0.}
                salvar_json(pasta/'estado.json',{'id':str(i),'id_ciclo':'sintetico','dataset':'sintetico','codigo':identidade({}),
                    'celula':celula,'status':'concluida_auditada','resultados':resultados,'financeiro':financeiro,
                    'referencia_constante':{'metricas_teste':m}})
                salvar_json(pasta/'integridade.json',{p.relative_to(pasta).as_posix():sha256(p) for p in pasta.rglob('*.parquet')})
            with patch('barreiras.consolidacao.RAIZ',Path(temporario)):
                r=consolidar(raiz)
                self.assertEqual(r['status'],'completo')
                self.assertEqual(r['celulas_auditadas'],4)
                self.assertEqual(r['contrastes_globais']['mamba_menos_lstm']['intervalos']['14']['log_loss'],[0.,0.])
                self.assertEqual(r['controles_comprar_manter'][0]['retorno_liquido'],0.)
                with (raiz/'0/mamba/previsoes_teste.parquet').open('ab') as f:
                    f.write(b'alterado')
                with self.assertRaisesRegex(ValueError,'Artefato alterado'):
                    consolidar(raiz)


if __name__=='__main__':
    unittest.main()
