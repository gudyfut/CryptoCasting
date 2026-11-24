"""Ensaio exclusivamente sintético do pós-processamento completo, sem GPU/treino."""
import tempfile,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,pandas as pd
from infraestrutura.artefatos import salvar_json
from avaliacao.metricas import calcular
from experimentos.entradas_niveis import publicacao as pub,ciclo

def run():
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);p=root/'dados/novo';pred=root/'dados/antigo';pp=pred/'publicacoes/tentativa_001';pp.mkdir(parents=True)
  reg=root/'registros/entradas_niveis';reg.mkdir(parents=True)
  (root/'docs').mkdir();salvar_json(root/'registros/catalogo_estudos.json',{})
  salvar_json(p/'progresso.json',{'status':'concluido'});salvar_json(p/'processo.json',{'ativo':False});salvar_json(reg/'execucao.json',{'id':'sintetico'})
  c=ciclo.configuracao();rconfig={b:{v:{'variante':v} for v in c['variantes_novas']} for b in c['blocos']}
  f={'id':'sintetico','contrato':{'configuracao':c,'receitas':rconfig}}
  pf={'id':'pred','contrato':{'receitas':{b:{'mse':{'variante':'mse'}} for b in c['blocos']},'carteira':{'pasta':'dummy','contrato':{'configuracao':{}}}}}
  ts=pd.date_range('2024-01-01T00:00Z',periods=48,freq='h');real=np.tile([-.01,.01],24)
  df=pd.DataFrame({'indice_candle':np.arange(48),'origem_utc':ts,'destino_utc':ts+pd.Timedelta(hours=24),'close':100.,'preco_destino':100*np.exp(real),'alvo':real})
  xs={}
  for b in c['blocos']:
   xs[b]={}
   for v in c['variantes']:
    xs[b][v]=SimpleNamespace(_conjunto=SimpleNamespace(partes={parte:df for parte in ['validacao','teste','operacional']}))
    for seed in c['seeds']:
     t=(pred/'celulas'/f'{b}_mse_{seed}' if v=='atual' else p/'celulas'/f'{b}_{v}_{seed}')/'tentativa_001';t.mkdir(parents=True)
     q=df.copy();q['previsao']=0.0001*c['variantes'].index(v)
     for parte in ['validacao','teste','operacional']:q.to_parquet(t/f'previsoes_{parte}.parquet',index=False)
     salvar_json(t/'resultado.json',{'metricas':{parte:calcular(q.alvo,q.previsao) for parte in ['validacao','teste']}})
     salvar_json(t/'conclusao.json',{'status':'concluido','arquivos':{}})
  resumo={'retorno_liquido':0.,'drawdown_minuto_close':.01,'exposicao_media':.5,'capital_final':10000.,'comissoes_usdt':0.,'slippage_usdt':0.}
  herdados={'carteiras':{}}
  for b in c['blocos']:
   for modelo,seeds in [('mse',c['seeds']),('benchmark',[None])]:
    for seed in seeds:
     for pol in (c['politicas'] if modelo=='mse' else ['comprar_manter','caixa']):
      for custo in c['cenarios']:herdados['carteiras'][f'{b}/{modelo}/{seed if seed is not None else "benchmark"}/{pol}/{custo}']=dict(resumo)
  def sim(*a):return dict(resumo),[],pd.DataFrame({'capital':[10000.]}),pd.DataFrame({'retorno_log':[0.]}),[]
  with patch.object(pub,'RAIZ',root),patch.object(pub,'REG',reg),patch.object(ciclo,'conferir_execucao',return_value=(p,f,xs)),patch.object(ciclo,'predecessora',return_value=(pred,pf,pp,herdados)),patch.object(pub,'conferir'),patch.object(pub,'auditar_ajuste',return_value={'natureza':'sintetico_mock'}),patch.object(pub,'carregar_minutos',return_value=(None,None)),patch.object(pub,'simular',side_effect=sim),patch.object(pub,'conferir_carteira',return_value={'status':'sintetico_mock'}):
   fim=pub.publicar();res=json.loads((root/fim['publicacao']/'resultados.json').read_text())
   assert len(res['por_ajuste'])==96 and len(res['carteiras'])==600
   assert len(res['contrastes']['teste'])==3 and len(res['auditoria'])==98
   assert len(res['medias_por_bloco'])==4 and all(len(x)==8 for b in res['medias_por_bloco'].values() for parte in b.values() for x in [parte['crua']['mse_por_seed']])
   assert (root/fim['relatorio']).is_file()
   try:pub.publicar()
   except FileExistsError:pass
   else:raise AssertionError('Publicação duplicada não bloqueada')
   return {'situacao':'aprovado','natureza':'sintetico_com_motor_auditoria_checkpoint_mockados','treinamentos':0,'ajustes_sinteticos_publicados':96,'controles_mockados':2,'carteiras_sinteticas':600,'contrastes':3,'relatorio_gerado':True,'duplicacao_bloqueada':True}
if __name__=='__main__':print(json.dumps(run(),indent=2))
