"""Testes de publicação/estatística; não altera recibo congelado do treinamento."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import consolidar_resultados as publicador
import auditar_publicacao as auditor
from consolidar_resultados import intervalo_blocos,curva_liquidacao
from previsao24.arquivos import salvar_json,ler_json,sha256,verificar_arquivos,identidade
from previsao24.configuracao import referencia,celulas,FOLDS
from previsao24.metricas import calcular

class ConsolidacaoTeste(unittest.TestCase):
    def test_bootstrap_constante(self):
        resultado=intervalo_blocos([(np.full(90,48.),np.full(90,24.)),(np.full(180,72.),np.full(180,24.))],14,2000,7)
        self.assertEqual(resultado['inferior'],2.5)
        self.assertEqual(resultado['superior'],2.5)

    def test_curva_caixa_usa_liquidacao_sem_alterar_capital(self):
        curva=[{'tempo_utc':'2023-01-02T00:01:00+00:00','capital':9900},
               {'tempo_utc':'2023-01-02T00:00:00+00:00','capital':9900},
               {'tempo_utc':'2023-01-03T00:00:00+00:00','capital':9900}]
        ajustada=curva_liquidacao(curva,1)
        self.assertEqual(len(ajustada),2)
        self.assertEqual(ajustada[0]['tempo_utc'],'2023-01-02T00:01:00+00:00')
        self.assertEqual(ajustada[-1]['capital'],9900)

    def test_fase_sintetica_inteira_publica_escores_pareados_e_financas(self):
        self.verificar_fase_sintetica()

    def test_lacuna_preserva_sinais_e_capital_desconhecido(self):
        self.verificar_fase_sintetica(com_lacuna=True)

    def verificar_fase_sintetica(self,com_lacuna=False):
        # Apenas em diretório temporário: estes dados nunca vão ao portal real.
        with tempfile.TemporaryDirectory() as temporario:
            raiz=Path(temporario)
            c=referencia()
            c.update(pares=['BTCUSDT'],contextos=[24,72],seeds=[17,42],folds_desenvolvimento=['DB1','DB2'])
            c['bootstrap']['replicas']=100
            pasta=raiz/'experimento'
            assinatura={'teste_sintetico':True,'com_lacuna':com_lacuna}
            id_dados=identidade(assinatura)[:20]
            salvar_json(raiz/'registros/execucao_atual.json',{'id':'sintetico','caminho':'experimento','dataset':id_dados})
            salvar_json(pasta/'execucao.json',{'assinatura':{'configuracao':c,'fontes':{},'dataset':id_dados},'dataset_caminho':'dataset'})
            salvar_json(pasta/'desenvolvimento_concluido.json',{'teste_sintetico':True})
            primeiro=int(pd.Timestamp('2023-01-01',tz='UTC').timestamp()//60)
            minutos=np.ones((181*1440,6),dtype=float)*100
            if com_lacuna:
                minutos[1441,:]=np.nan
            (raiz/'dataset/BTCUSDT').mkdir(parents=True)
            np.save(raiz/'dataset/BTCUSDT/minutos.npy',minutos)
            salvar_json(raiz/'dataset/dataset.json',{'primeiro_minuto':primeiro,'id':id_dados,'assinatura':assinatura,
                        'arquivos':{'BTCUSDT/minutos.npy':sha256(raiz/'dataset/BTCUSDT/minutos.npy')}})
            grade=celulas(c,'desenvolvimento')+[{'par':'BTCUSDT','fold':f,'modelo':m} for f in c['folds_desenvolvimento'] for m in ('arima','naive')]
            for i,x in enumerate(grade):
                local=pasta/'celulas'/str(i)/'tentativa_001'
                origem=pd.date_range(FOLDS[x['fold']][1],pd.Timestamp(FOLDS[x['fold']][2])-pd.Timedelta(hours=24),freq='h',inclusive='left',tz='UTC')
                y=np.where(np.arange(len(origem))%2==0,.02,-.02)
                p=y+(.001 if x['modelo']=='mamba' else .002) if x['modelo'] in ('lstm','mamba') else np.zeros(len(y))
                q=pd.DataFrame({'origem_utc':origem,'alvo':y,'previsao':p})
                salvar_json(local/'tentativa.json',{'celula':x,'status':'auditada','teste_sintetico':True})
                q.to_parquet(local/'previsoes_teste.parquet',index=False)
                q.to_parquet(local/'previsoes_operacional.parquet',index=False)
                salvo={'metricas':{'teste':calcular(y,p)}}
                if x['modelo']=='arima':
                    salvo.update(ordem=[0,1,0],candidatos_validos=9,candidatos_falhos=0)
                    salvar_json(local/'candidatos.json',{'candidatos':[{'ordem':o} for o in c['arima']['ordens']]})
                salvar_json(local/'resultado.json',salvo)
                salvar_json(local/'auditoria.json',{'arquivos':{p.name:sha256(p) for p in local.iterdir() if p.name!='tentativa.json'}})
            with patch.object(publicador,'RAIZ',raiz):
                publicador.consolidar('desenvolvimento')
            destino=raiz/'registros/analises/sintetico/desenvolvimento'
            resumo=ler_json(destino/'resumo.json')
            self.assertEqual(len(resumo['ajustes']),20)
            self.assertEqual(len(resumo['metricas']),16)
            mamba=next(r for r in resumo['modelos'] if r['modelo']=='mamba')
            self.assertAlmostEqual(mamba['mse'],.001**2)
            self.assertAlmostEqual(mamba['habilidade_mse'],1-.001**2/.02**2)
            contraste=next(r for r in resumo['contrastes'] if r['contraste']=='mamba_menos_lstm')
            self.assertAlmostEqual(contraste['diferenca'],-3e-6)
            self.assertTrue(all(i['superior']<0 for i in contraste['intervalos']))
            caixa=[r for r in resumo['financeiro'] if r['modelo']=='naive']
            self.assertTrue(all(r['capital_final']==10000 and r['entradas_planejadas']==0 for r in caixa))
            for estrategia in resumo['financeiro']:
                if estrategia['modelo']=='mamba':
                    f=c['operacao']['taxa'] if estrategia['cenario']=='base' else c['operacao']['taxa_agravada']
                    s=c['operacao']['slippage'] if estrategia['cenario']=='base' else c['operacao']['slippage_agravado']
                    fator=(1-s)*(1-f)/((1+s)*(1+f))
                    self.assertEqual(estrategia['entradas_planejadas'],179)
                    if com_lacuna:
                        self.assertIsNone(estrategia['capital_final'])
                        self.assertIsNone(estrategia['retorno_liquido'])
                    else:
                        self.assertAlmostEqual(estrategia['capital_final'],10000*fator**estrategia['entradas_planejadas'],places=7)
                operacao=ler_json(destino/estrategia['arquivo'])
                tempos=[p['tempo_utc'] for p in operacao['curva']]
                self.assertEqual(tempos,sorted(set(tempos)))
            verificar_arquivos(destino,ler_json(destino/'publicacao.json')['arquivos'])
            with patch.object(auditor,'RAIZ',raiz):
                auditor.auditar('desenvolvimento')
            self.assertEqual(ler_json(destino/'auditoria_publicacao.json')['status'],'aprovado')
            if not com_lacuna:
                # Escalar ambas as cotações preserva o retorno: conferir somente
                # as contas não detectaria este descolamento do mercado.
                estrategia=next(r for r in resumo['financeiro'] if r['modelo']=='mamba')
                caminho=destino/estrategia['arquivo']
                conteudo=ler_json(caminho)
                conteudo['ordens'][0]['preco_entrada']*=2
                conteudo['ordens'][0]['preco_saida']*=2
                salvar_json(caminho,conteudo)
                manifesto_publicado=ler_json(destino/'publicacao.json')
                manifesto_publicado['arquivos'][estrategia['arquivo']]=sha256(caminho)
                salvar_json(destino/'publicacao.json',manifesto_publicado)
                with patch.object(auditor,'RAIZ',raiz),self.assertRaisesRegex(ValueError,'Preços publicados diferem'):
                    auditor.auditar('desenvolvimento')
            # Uma alteração posterior dos preços deve impedir publicação e aceite.
            with (raiz/'dataset/BTCUSDT/minutos.npy').open('ab') as arquivo:
                arquivo.write(b'alterado')
            with patch.object(publicador,'RAIZ',raiz),self.assertRaisesRegex(ValueError,'Artefato ausente/alterado'):
                publicador.consolidar('desenvolvimento')
            with patch.object(auditor,'RAIZ',raiz),self.assertRaisesRegex(ValueError,'Artefato ausente/alterado'):
                auditor.auditar('desenvolvimento')

if __name__=='__main__':
    unittest.main()
