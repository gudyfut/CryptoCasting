"""Treinamento sem consulta ao teste para seleção de época."""
from __future__ import annotations

import os
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .arquivos import agora, salvar_json
from .metricas import calcular, erros
from .redes import criar


def fixar_seed(seed):
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.use_deterministic_algorithms(True,warn_only=True)
    torch.set_num_threads(2)


class Janelas(Dataset):
    def __init__(self,matriz,quadro,contexto,escalas):
        self.matriz=torch.as_tensor(matriz,dtype=torch.float32)
        self.indices=quadro['indice_hora'].to_numpy(np.int64)
        self.aux=((np.log(quadro['distancia'].to_numpy())-escalas['media_aux'])/escalas['escala_aux']).astype(np.float32)
        self.y=quadro['classe'].to_numpy(np.int64)
        self.contexto=contexto
        if len(self.indices) and self.indices.min()<contexto-1:
            raise ValueError('Janela atravessa início dos dados.')
        if not np.isfinite(self.aux).all():
            raise ValueError('Variável auxiliar não finita.')

    def __len__(self):
        return len(self.indices)

    def __getitem__(self,i):
        fim=self.indices[i]+1
        return self.matriz[fim-self.contexto:fim],torch.tensor([self.aux[i]]),self.y[i]


def carregador(matriz,q,w,escalas,batch,treino=False,seed=42,cuda=False):
    return DataLoader(Janelas(matriz,q,w,escalas),batch_size=batch,shuffle=treino,
          num_workers=0,drop_last=False,pin_memory=cuda,
          generator=torch.Generator().manual_seed(seed))


def prever(rede,loader,dispositivo):
    rede.eval()
    valores=[]
    with torch.inference_mode():
        for x,a,_ in loader:
            logits=rede(x.to(dispositivo,non_blocking=True),a.to(dispositivo,non_blocking=True))
            if not torch.isfinite(logits).all():
                raise ValueError('Logits não finitos.')
            valores.append(torch.softmax(logits,dim=1).cpu().numpy())
    if not valores:
        return np.empty((0,3),np.float32)
    return np.concatenate(valores)


def treinar(nome,c,celula,matriz,blocos,escalas,destino: Path):
    fixar_seed(celula['seed'])
    dispositivo=torch.device(c['dispositivo'])
    if dispositivo.type=='cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível; execução não pode trocar de backend.')
    destino.mkdir(parents=True,exist_ok=True)
    t=c['treino']
    rede=criar(nome,c).to(dispositivo)
    otimizador=torch.optim.AdamW(rede.parameters(),lr=t['taxa_aprendizado'],
                               weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
    loaders={b:carregador(matriz,q,celula['contexto'],escalas,t['batch'] if b=='treino' else t['microbatch'],
                         b=='treino',celula['seed'],dispositivo.type=='cuda') for b,q in blocos.items()}
    melhor=float('inf')
    espera=0
    historico=[]
    inicio=time.perf_counter()
    if dispositivo.type=='cuda':
        torch.cuda.reset_peak_memory_stats()
    for epoca in range(1,t['epocas']+1):
        rede.train()
        soma=0.0
        n=0
        for x,a,y in loaders['treino']:
            otimizador.zero_grad(set_to_none=True)
            tamanho=len(y)
            for i in range(0,tamanho,t['microbatch']):
                fim=min(i+t['microbatch'],tamanho)
                logits=rede(x[i:fim].to(dispositivo,non_blocking=True),a[i:fim].to(dispositivo,non_blocking=True))
                perda=nn.functional.cross_entropy(logits,y[i:fim].to(dispositivo,non_blocking=True),reduction='sum')
                if not torch.isfinite(perda):
                    raise ValueError('Perda não finita.')
                (perda/tamanho).backward()
                soma+=float(perda.detach().cpu())
            nn.utils.clip_grad_norm_(rede.parameters(),t['clipping'],error_if_nonfinite=True)
            otimizador.step()
            n+=tamanho
        pv=prever(rede,loaders['validacao'],dispositivo)
        perda_val=float(erros(blocos['validacao']['classe'],pv)[0].mean())
        melhorou=perda_val<melhor
        if melhorou:
            melhor=perda_val
            espera=0
            temporario=destino/'checkpoint.parcial'
            metadados=json.loads(json.dumps({'epoca':epoca,'log_loss_validacao':melhor,
                        'configuracao':c,'celula':celula,'escalas':escalas,'modelo':nome},allow_nan=False))
            torch.save({'pesos':rede.state_dict(),**metadados},temporario)
            temporario.replace(destino/'checkpoint.pt')
        else:
            espera+=1
        linha={'epoca':epoca,'treino_log_loss':soma/n,'validacao_log_loss':perda_val,
               'melhorou':melhorou,'segundos_acumulados':time.perf_counter()-inicio,'utc':agora()}
        historico.append(linha)
        salvar_json(destino/'epocas.json',historico)
        print(f"{nome} {celula} época={epoca} treino={soma/n:.6f} validação={perda_val:.6f} espera={espera}",flush=True)
        if espera>=t['paciencia']:
            break
    checkpoint=torch.load(destino/'checkpoint.pt',map_location=dispositivo,weights_only=True)
    rede.load_state_dict(checkpoint['pesos'])
    metricas={}
    previsoes={}
    for bloco in ('validacao','teste','operacional'):
        p=prever(rede,loaders[bloco],dispositivo)
        q=blocos[bloco].copy()
        for k in range(3):
            q[f'p{k}']=p[:,k]
        q['modelo']=nome
        q.to_parquet(destino/f'previsoes_{bloco}.parquet',index=False)
        previsoes[bloco]=q
        if bloco!='operacional':
            metricas[bloco]=calcular(q['classe'],p,q['ambiguo'])
    # Outra instância deve reproduzir exatamente as previsões do checkpoint.
    recarregada=criar(nome,c).to(dispositivo)
    recarregada.load_state_dict(torch.load(destino/'checkpoint.pt',map_location=dispositivo,weights_only=True)['pesos'])
    refeito=prever(recarregada,loaders['teste'],dispositivo)
    original=previsoes['teste'][['p0','p1','p2']].to_numpy()
    diferenca=float(np.abs(refeito-original).max())
    if not np.array_equal(refeito,original):
        raise ValueError(f'Recarga divergiu: diferença máxima {diferenca}.')
    resultado={'modelo':nome,'epoca_selecionada':checkpoint['epoca'],'epocas_executadas':len(historico),
               'parametros':sum(p.numel() for p in rede.parameters()),'metricas':metricas,
               'segundos':time.perf_counter()-inicio,'recarga_exata':True,
               'memoria_cuda_maxima_bytes':torch.cuda.max_memory_allocated() if dispositivo.type=='cuda' else None}
    salvar_json(destino/'resultado_modelo.json',resultado)
    del rede,recarregada,otimizador
    if dispositivo.type=='cuda':
        torch.cuda.empty_cache()
    return resultado,previsoes
