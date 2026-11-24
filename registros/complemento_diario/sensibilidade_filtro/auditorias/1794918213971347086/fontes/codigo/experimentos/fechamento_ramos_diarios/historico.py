"""Consolida sondas existentes com origem explícita; não roda redes ou otimização."""
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora
from .contratos import REG


def consolidar():
    destino=REG/'diagnostico_previo.json'
    assert not destino.exists(),'Não sobrescrever diagnóstico publicado.'
    fonte='registros/padronizacao_diaria/diagnosticos/2026-11-08T200124.658529Z/trajetoria.json'
    t=ler_json(RAIZ/fonte);fontes={fonte:sha256(RAIZ/fonte)};trajetorias={}
    for seed,registro in t['trajetorias']['padronizado'].items():
        sondas=registro['sondas_treino32']
        trajetorias[seed]=[dict(checkpoint=s['checkpoint'],max_delta_sem_ramos=s['max_delta_sem_mamba'],
            rms_delta_sem_ramos=s['rms_delta_sem_mamba'],norma_layernorm=s['normas']['layernorm']['norma'],
            norma_outros_mamba=s['normas']['outros_mamba']['norma'],
            norma_lineares=s['normas']['lineares']['norma']) for s in sondas]
    sondas={}
    for estudo,variantes in [('eixo_temporal_diario',['A','B','C','D']),
                            ('penalizacao_seletiva_diaria',['A','S'])]:
        ptr=ler_json(RAIZ/f'registros/{estudo}/execucao.json');p=RAIZ/ptr['pasta']
        assert ler_json(p/'fechamento.json')['situacao']=='concluido_conferido'
        for v in variantes:
            for seed in (42,17,2026):
                ar=p/'publicacao/observacoes'/f'{v}_{seed}.json';q=ler_json(ar)
                fontes[ar.relative_to(RAIZ).as_posix()]=sha256(ar)
                sondas[f'{estudo}/{v}_{seed}']=dict(epoca=q['epoca'],
                    populacao=q['populacao'],normas=q['normas'],contribuicao=q['contribuicao_ramos'])
    ptr=ler_json(RAIZ/'registros/ablacao_linear_diaria/execucao.json')
    ar=RAIZ/ptr['pasta']/'publicacao/diagnostico_afim.json'
    afim=ler_json(ar);fontes[ar.relative_to(RAIZ).as_posix()]=sha256(ar)
    r=dict(utc=agora(),fontes=fontes,trajetoria_padronizacao=trajetorias,sondas_anteriores=sondas,
        intervencao_populacoes_completas=afim,novos_treinos=0,novas_inferencias=0,
        observacoes=['Ramos tinham efeito mensurável inicialmente no BTC padronizado e perderam contribuição nas sondas salvas.',
                    'A redução das normas LayerNorm acompanha a supressão; associação não isola a causa em um parâmetro.',
                    'B sem penalização conserva atividade nas sondas, sem superioridade já estabelecida.',
                    'A/L foram conferidos em todas as populações no ciclo de ablação anterior.'],
        limites='A trajetória usa checkpoints de melhoria disponíveis e sondas de32janelas; não reconstrói todas as épocas. Não generalizar atividade/zero das sondas à população sem intervenção completa. Nenhum novo modelo ou resultado de2026.')
    salvar_json(destino,r);print('DIAGNOSTICO_PREVIO',len(fontes),'fontes',flush=True)


if __name__=='__main__':consolidar()
