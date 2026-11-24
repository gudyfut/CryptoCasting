"""Novas divisões/escalas; receitas e artefatos anteriores permanecem intactos."""
from copy import deepcopy
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade
from entradas_modelo import preparar_entradas
from entradas_modelo.conjunto import ConjuntoEntradas
from modelos.consumo import ConsumoModelos

REG = RAIZ / 'registros/huber_blocos'
CONFIG = 'configuracoes/huber_blocos_001.json'
SEEDS = [17,42,2026,7,123,31415,271828,161803]


def configuracao():
    c = ler_json(RAIZ / CONFIG)
    assert c['seeds'] == SEEDS and c['ordem_seeds'] == [42,17,2026,7,123,31415,271828,161803]
    assert c['variantes'] == ['mse','huber'] and list(c['blocos']) == ['B1','B2','B3','B4']
    datas = [('2023-10-01','2024-01-01','2024-07-01'),('2024-04-01','2024-07-01','2025-01-01'),
             ('2024-10-01','2025-01-01','2025-07-01'),('2025-04-01','2025-07-01','2026-01-01')]
    for b, (a,t,z) in zip(c['blocos'], datas):
        assert c['blocos'][b] == {'treino':['2021-01-01T00:00:00Z',a+'T00:00:00Z'],
            'validacao':[a+'T00:00:00Z',t+'T00:00:00Z'],'teste':[t+'T00:00:00Z',z+'T00:00:00Z']}
    assert (c['ajustes_principais'],c['controles_reais'],c['ajustes_reais_total']) == (64,2,66)
    assert c['controle_bloco']=='B1' and c['controle_seed']==42 and c['simulacoes_total']==408
    assert c['politicas']==['smart','diaria24'] and c['cenarios']==['ideal','base','agravado']
    assert c['carteira_execucao']=='dados/experimentos/backtest_carteira_8ec8a66648313caa48e3'
    assert c['bootstrap']=={'dias':[7,14,28],'principal':14,'replicas':2000,'seed':20261103,'principal_seeds_e_tempo':True}
    return c


def receita(c, bloco, variante):
    r = deepcopy(ler_json(RAIZ / c['receita_base']))
    # Evita transportar o significado antigo dos metadados de três seeds/R0.
    r.update(versao='huber-blocos-1',ciclo=c['ciclo'],seeds=c['seeds'],seeds_pareadas=c['seeds'],
             divisao=c['blocos'][bloco],bloco=bloco,variante=variante,
             referencia_execucao='nova_comparacao_pareada_em_blocos',
             controle='Dois controles reais B1/42, além de reprodução sintética; 66 ajustes no total.')
    if variante=='mse':r['perda']={'nome':'MSELoss','alvo':'padronizado_treino'}
    elif variante!='huber':raise ValueError('Perda desconhecida.')
    assert r['mamba']['estado']==16 and r['treino']=={
        'epocas':100,'paciencia':10,'batch':64,'microbatch':32,'taxa_aprendizado':.0002,'weight_decay':.001,'clipping':1.}
    return r


def preparar_dados():
    c = configuracao()
    saida = {}
    for b, divisao in c['blocos'].items():
        r = ler_json(RAIZ / c['entradas_base']);r['divisao']=divisao
        p = preparar_entradas(RAIZ/c['candles_pasta'],r)
        saida[b] = {'pasta':p.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(p/'manifesto.json')}
        salvar_json(REG/'preparacao_dados_progresso.json',{'concluidos':saida,'total':4})
        print('Entradas preparadas:',b,saida[b]['pasta'],flush=True)
    if (REG/'entradas.json').exists():
        assert ler_json(REG/'entradas.json')==saida
    else:salvar_json(REG/'entradas.json',saida)
    return saida


class Verificador:
    """Deduplicação apenas dentro de uma conferência; nova fase usa novo objeto."""
    def __init__(self):
        self.arquivos={};self.prontos=set();self.pilha=set()

    def arquivos_em(self, base, mapa):
        base=Path(base).resolve()
        for nome,h in mapa.items():
            p=(base/nome).resolve()
            if not p.is_relative_to(base):raise ValueError('Caminho fora da base.')
            if p in self.arquivos:
                if self.arquivos[p]!=h:raise ValueError('Hashes conflitantes.')
            else:
                if not p.is_file() or sha256(p)!=h:raise ValueError(f'Artefato ausente/alterado: {p}')
                self.arquivos[p]=h

    def artefato(self,p):
        p=Path(p).resolve()
        if p in self.pilha:raise ValueError('Dependência circular.')
        if p in self.prontos:return ler_json(p/'manifesto.json')
        self.pilha.add(p);m=ler_json(p/'manifesto.json')
        assert identidade(m['assinatura'])[:20]==m['id']
        self.arquivos_em(p,m['arquivos'])
        self.arquivos_em(p/'fontes',m['assinatura']['fontes'])
        self.arquivos_em(RAIZ,m['assinatura'].get('originais',{}))
        for d in m['assinatura'].get('dependencias',[]):
            q=RAIZ/d['pasta'];self.arquivos_em(q,{'manifesto.json':d['manifesto_sha256']});self.artefato(q)
        self.pilha.remove(p);self.prontos.add(p)
        return m


def carregar_blocos(mapa, verificador=None):
    v=verificador or Verificador();saida={}
    for b,d in mapa.items():
        p=RAIZ/d['pasta'];v.arquivos_em(p,{'manifesto.json':d['manifesto_sha256']})
        assert v.artefato(p)['tipo']=='entradas_modelo'
        q=ConjuntoEntradas(np.load(p/'entradas.npy',allow_pickle=False),pd.read_parquet(p/'origens.parquet'),
            {x:pd.read_parquet(p/f'{x}.parquet') for x in ('treino','validacao','teste','operacional')},
            ler_json(p/'escalas.json'),ler_json(p/'contrato.json'))
        saida[b]=ConsumoModelos(q,d['manifesto_sha256'])
    return saida


def conferir_escalas_reais(c,consumos):
    """Refaz as fórmulas e a união de horas de treino, sem chamar a receita."""
    q=pd.read_parquet(RAIZ/c['candles_pasta']/'BTCUSDT.parquet')
    anterior=q.close.shift(1).to_numpy(float)
    with np.errstate(invalid='ignore',divide='ignore'):
        raw=np.column_stack([np.log(q[n].to_numpy(float)/anterior) for n in ('open','high','low','close')]+[np.log1p(q.volume.to_numpy(float))])
    raw[~np.isfinite(q[['open','high','low','close','volume']].to_numpy()).all(axis=1)]=np.nan
    y=np.log(q.close.shift(-24).to_numpy()/q.close.to_numpy())
    resultado={}
    for b,consumo in consumos.items():
        conjunto=consumo._conjunto;indices=conjunto.partes['treino'].indice_candle.to_numpy();usados=np.zeros(len(q),bool)
        for i in indices:usados[i-167:i+1]=True
        m=raw[usados].mean(axis=0);s=raw[usados].std(axis=0);s=np.where(s==0,1.,s)
        e=conjunto.escalas
        np.testing.assert_allclose(m,e['media_entrada'],rtol=1e-13,atol=1e-14)
        np.testing.assert_allclose(s,e['escala_entrada'],rtol=1e-13,atol=1e-14)
        np.testing.assert_allclose(y[indices],conjunto.partes['treino'].alvo.to_numpy(),rtol=1e-13,atol=1e-14)
        np.testing.assert_allclose([y[indices].mean(),y[indices].std()],[e['media_alvo'],e['escala_alvo']],rtol=1e-13,atol=1e-14)
        np.testing.assert_array_equal(((raw-m)/s).astype(np.float32),conjunto.matriz)
        resultado[b]={'matriz_reproduzida_exatamente':True,'horas_unicas_treino':int(usados.sum()),'alvos_e_scalers_recalculados':True}
    return resultado
