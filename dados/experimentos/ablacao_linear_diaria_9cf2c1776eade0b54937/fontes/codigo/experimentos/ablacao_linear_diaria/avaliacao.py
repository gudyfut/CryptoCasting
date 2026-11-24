"""Mesmo avaliador financeiro/preditivo; diagnóstico afim adicional sem ajuste."""
from types import FunctionType
import numpy as np
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json
from experimentos.penalizacao_seletiva_diaria import avaliacao as herdado
from .contratos import receita
from .treinamento import carregar_rede, inferir
from .modelo import coeficientes_afins


def diagnosticar(p, c, dados):
    caminhos = ler_json(p/'modelos.json'); resultado = {}
    for variante in c['variantes']:
        for seed in c['seeds']:
            chave = f'{variante}_{seed}'
            rede = carregar_rede(RAIZ/caminhos[chave]['pasta'], receita(c,variante))
            pesos = {k:v.clone() for k,v in rede.state_dict().items()}
            coef, intercepto = coeficientes_afins(rede)
            entrada = {'parametros':sum(v.numel() for v in rede.parameters()),
                       'coeficientes_canal_dia':coef.tolist(), 'intercepto':intercepto, 'fases':{}}
            for fase,z in dados.items():
                completo = inferir(rede,z['x'])
                hooks = [m.register_forward_hook(lambda m,a,o:torch.zeros_like(o))
                         for m in rede.modules() if isinstance(m,Mamba)]
                try: residual = inferir(rede,z['x'])
                finally:
                    for h in hooks:h.remove()
                afim = np.einsum('nct,ct->n',z['x'].astype(np.float64),coef)+intercepto
                np.testing.assert_allclose(residual,afim,atol=2e-6,rtol=1e-5)
                entrada['fases'][fase] = {
                    'exemplos':len(completo),
                    'max_diferenca_sem_ramos':float(abs(completo-residual).max()),
                    'rms_diferenca_sem_ramos':float(np.sqrt(np.mean((completo-residual)**2))),
                    'max_residuo_afim_float64':float(abs(residual-afim).max())}
            assert all(torch.equal(v,rede.state_dict()[k]) for k,v in pesos.items())
            resultado[chave] = entrada
            del rede;torch.cuda.empty_cache()
    salvar_json(p/'publicacao/diagnostico_afim.json',{
        'modelos':resultado,'atualizacoes_de_pesos':0,
        'limites':'Diagnóstico em todas as populações preservadas. L não tem ramos por construção; atividade zero não é colapso aprendido. Decomposição float64 inclui arredondamento frente ao forward float32. Não prova equivalência estatística nem inutilidade universal do SSM.'})


def executar(p,c,dados,f,progresso):
    # O corpo bytecode é o do avaliador aprovado. Só resolver .treinamento e
    # receita neste namespace, sem alterar o módulo da experiência anterior.
    globais = dict(herdado.executar.__globals__)
    globais.update(__package__=__package__, receita=receita)
    funcao = FunctionType(herdado.executar.__code__,globais,herdado.executar.__name__,
                          herdado.executar.__defaults__,herdado.executar.__closure__)
    resultado = funcao(p,c,dados,f,progresso)
    diagnosticar(p,c,dados)
    return resultado
