"""Inferência/backward diagnóstico em checkpoint concluído; sem otimizador/novo ajuste."""
import argparse
import shutil
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora,conferir_arquivos
from treinamento.preservacao import conferir
from treinamento.otimizacao import fixar_seed
from modelos.contratos import EspecificacaoModelo
from modelos.neurais import restaurar_pesos
from experimento_cryptomamba.modelo import criar_rede


def diagnosticar(seed):
    import torch
    reg=RAIZ/'registros/cryptomamba'
    ptr=ler_json(reg/'execucao.json');base=RAIZ/ptr['pasta'];f=ler_json(base/'congelamento.json')
    conferir_arquivos(base,{'congelamento.json':ptr['congelamento_sha256']})
    conferir_arquivos(RAIZ,f['contrato']['fontes'])
    ts=[t for t in (base/'celulas'/f'cryptomamba_{seed}').glob('tentativa_*') if (t/'conclusao.json').exists()]
    if len(ts)!=1:raise ValueError('Diagnosticar apenas seed concluída e inequívoca.')
    t=ts[0];conferir(t);sel=ler_json(t/'selecao.json');conferir_arquivos(t,{sel['arquivo']:sel['sha256']})
    pacote=torch.load(t/sel['arquivo'],map_location='cpu',weights_only=True)['modelo']
    assert pacote['especificacao']['identidade']==f['contrato']['consumo']
    cfg=f['contrato']['configuracao'];espec=EspecificacaoModelo(**pacote['especificacao'])
    dados=RAIZ/cfg['entradas_pasta'];conferir_arquivos(dados,ler_json(dados/'manifesto.json')['arquivos'])
    q=pd.read_parquet(dados/'validacao.parquet');pos=np.linspace(0,len(q)-1,8,dtype=int);indices=q.iloc[pos].indice_candle.to_numpy(int)
    matriz=np.load(dados/'entradas.npy',allow_pickle=False)
    x=torch.tensor(np.stack([matriz[i-espec.contexto+1:i+1] for i in indices]),device='cuda')
    fixar_seed(seed);inicial=criar_rede(espec,cfg)
    treinada=criar_rede(espec,cfg);restaurar_pesos(treinada,pacote)
    def medir(rede):
        camadas={};ganchos=[]
        def registrar(nome):
            def capturar(mod,args,saida):
                z=saida.detach();camadas[nome]={'forma':list(z.shape),'maior_desvio_entre_janelas':float(z.std(dim=0,unbiased=False).abs().max().cpu()),'maior_valor_absoluto':float(z.abs().max().cpu())}
            return capturar
        for nome,mod in [('adaptacao_temporal',rede.adaptacao_temporal)]+[(f'cblock_{i}',b) for i,b in enumerate(rede.nucleo.blocks)]+[('merge',rede.nucleo.post_process)]:
            ganchos.append(mod.register_forward_hook(registrar(nome)))
        with torch.inference_mode():z=rede(x).cpu().numpy().astype(float)
        for h in ganchos:h.remove()
        pesos={n:{'norma_l2':float(p.detach().norm().cpu()),'maior_absoluto':float(p.detach().abs().max().cpu())} for n,p in rede.named_parameters() if n.endswith('norm.weight') or n in ('adaptacao_temporal.weight','nucleo.post_process.1.weight')}
        return {'camadas':camadas,'saidas_padronizadas':z.tolist(),'desvio_saida':float(np.std(z)),'valores_distintos':len(np.unique(z)),'pesos':pesos}
    a,b=medir(inicial),medir(treinada)
    entrada=x.detach().clone().requires_grad_(True);treinada(entrada).sum().backward()
    grad={'maior_absoluto':float(entrada.grad.abs().max().cpu()),'norma_l2':float(entrada.grad.norm().cpu())}
    indice=ler_json(reg/'sensibilidade_atual.json') if (reg/'sensibilidade_atual.json').exists() else {}
    if str(seed) in indice:raise FileExistsError('Diagnóstico já existe; preservar.')
    d=reg/'diagnosticos_sensibilidade'/uuid4().hex;d.mkdir(parents=True)
    r={'utc':agora(),'execucao':ptr['id'],'seed':seed,'checkpoint_sha256':sel['sha256'],'origens_utc':q.iloc[pos].origem_utc.astype(str).tolist(),
        'entrada_forma':list(x.shape),'entrada_maior_desvio_entre_janelas':float(x.std(dim=0,unbiased=False).max().cpu()),'inicial':a,'treinada':b,'gradiente_saida_soma_em_relacao_entradas':grad,
        'natureza':'Oito janelas reais só de passado; comparação inicial/checkpoint e derivada, sem otimizador ou treinamento adicional.',
        'limites':'Diagnóstico posterior de sensibilidade, não prova causal isolada de Adam/decay/perda/arquitetura; não muda receita ou seleção.'}
    salvar_json(d/'sensibilidade.json',r);shutil.copy2(__file__,d/'verificador.py')
    salvar_json(d/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in d.iterdir() if p.is_file()}})
    indice[str(seed)]={'arquivo':(d/'sensibilidade.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'sensibilidade.json')};salvar_json(reg/'sensibilidade_atual.json',indice)
    print({'seed':seed,'arquivo':indice[str(seed)],'inicial_distintos':a['valores_distintos'],'treinada_distintos':b['valores_distintos'],'gradiente':grad})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed',type=int,required=True)
    diagnosticar(p.parse_args().seed)
