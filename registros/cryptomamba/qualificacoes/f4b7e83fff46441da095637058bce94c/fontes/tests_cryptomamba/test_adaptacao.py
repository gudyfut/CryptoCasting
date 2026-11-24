from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,conferir_arquivos,sha256
from modelos.consumo import ConsumoModelos
from tests_modelos.apoio import conjunto
from tests_taxa_aprendizado.test_ciclo import refs_artificiais
from experimento_cryptomamba import ciclo
from experimento_cryptomamba.publicacao import metricas_preco


def refs_sinteticas():
    r=refs_artificiais();r.update({f'taxa0001_estado{n}_{s}':r['estado16_42'] for n in (8,16,32,64) for s in ciclo.SEEDS});return r


class Adaptacao(unittest.TestCase):
    def test_contrato_configuracao_sem_mudar_populacao(self):
        c=ciclo.configuracao();self.assertEqual(c['arquitetura']['varredura'],'canais');self.assertEqual(c['contexto'],168);self.assertEqual(c['treino']['taxa_aprendizado'],.01)
        original=ciclo.ler_json
        def mudar(p):
            x=original(p)
            if Path(p).name==Path(ciclo.CONFIG).name:x['contexto']=14
            return x
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao()

    def test_dimensoes_e_grupos_adam_scheduler(self):
        import torch
        from experimento_cryptomamba.modelo import criar_rede
        from experimento_cryptomamba.treino import otimizador
        c=ciclo.configuracao();consumo=ConsumoModelos(conjunto(),'sintetico');rede=criar_rede(consumo.especificacao,c)
        shapes=[];h=rede.nucleo.blocks[0][0].op.register_forward_pre_hook(lambda mod,args:shapes.append(list(args[0].shape)))
        x=torch.randn(2,168,5,device='cuda');y=rede(x);h.remove();self.assertEqual(list(y.shape),[2]);self.assertEqual(shapes,[[2,5,14]])
        self.assertEqual(sum(p.numel() for p in rede.parameters()),139317)
        opt,grupos=otimizador(rede,c);self.assertIsInstance(opt,torch.optim.Adam);self.assertNotIsInstance(opt,torch.optim.AdamW)
        marcados={nome for nome,p in rede.named_parameters() if getattr(p,'_no_weight_decay',False)}
        self.assertEqual(len(marcados),24);self.assertTrue(all(g['weight_decay']==0 for g in grupos if g['nome'] in marcados))
        sch=torch.optim.lr_scheduler.StepLR(opt,10,.5)
        for _ in range(10):opt.zero_grad(set_to_none=True);opt.step();sch.step()
        self.assertAlmostEqual(opt.param_groups[0]['lr'],.005)

    def test_preco_mape_e_retorno_zero(self):
        q=pd.DataFrame({'close':[100.,100.],'preco_destino':[100.,102.],'previsao':[0.,np.log(1.02)]})
        r=metricas_preco(q);self.assertLess(r['mape_percentual'],1e-12);self.assertLess(r['rmse_usdt'],1e-12)
        q.loc[0,'preco_destino']=0
        with self.assertRaises(ValueError):metricas_preco(q)

    def test_autorizacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.json';a={'execucao':'id','seeds':ciclo.SEEDS,'ajustes_reais_total':6,'abordagem':'cryptomamba_adaptado','mensagem_usuario':'fixture'}
            salvar_json(p,a);ciclo.validar_autorizacao(p,'id')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'outro')
            a['ajustes_reais_total']=12;salvar_json(p,a)
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'id')

    def test_executor_seis_publica59_e_nao_reexecuta(self):
        c=ciclo.configuracao();consumo=ConsumoModelos(conjunto(),'sintetico');refs=refs_sinteticas();antes={k:sha256(p/'conclusao.json') for k,p in refs.items()}
        c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()};c['bootstrap']['replicas']=5
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);f={'id':'fixture','contrato':{'configuracao':c,'fontes':{}}};salvar_json(p/'progresso.json',{'status':'preparado'});salvar_json(p/'a.json',{'execucao':'fixture','seeds':ciclo.SEEDS,'ajustes_reais_total':6,'abordagem':'cryptomamba_adaptado','mensagem_usuario':'fixture'});chamadas=[]
            def ajustar(consumo,s,*args):chamadas.append(s);return None,{'parametros':139317}
            def avaliar(consumo,partes,c,t,*args):
                for n in ('resultado.json','previsoes_validacao.parquet','previsoes_teste.parquet','previsoes_operacional.parquet'):shutil.copy2(refs['estado16_42']/n,t/n)
            minutos=np.ones((31*1440,6));minutos[:,:4]=100;primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,consumo,consumo._conjunto.partes,refs)),patch.object(ciclo,'ajustar',side_effect=ajustar),patch.object(ciclo,'avaliar',side_effect=avaliar),patch('experimento_cryptomamba.publicacao.carregar_minutos',return_value=(minutos,primeiro)):
                ciclo.executar(p/'a.json');self.assertEqual(chamadas,ciclo.ORDEM)
                with self.assertRaises(ValueError):ciclo.executar(p/'a.json',True)
            pub=p/ler_json(p/'publicacao.json')['pasta'];conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos']);r=ler_json(pub/'resultados.json');self.assertEqual((r['novos'],r['herdados']),(6,53));self.assertEqual(len(r['por_ajuste']),59)
            self.assertEqual(r['medias']['teste']['naive']['n_seeds'],1);self.assertIsNone(r['medias']['teste']['naive']['metricas']['mse_desvio_seeds'])
            from experimento_cryptomamba import finalizacao
            (p/'docs').mkdir()
            with patch.object(finalizacao,'RAIZ',p):finalizacao.relatar(r,{'id':'fixture'},{'arquivo':'audit.json'},{'arquivo':'comp.json'})
        self.assertEqual(antes,{k:sha256(p/'conclusao.json') for k,p in refs.items()})
