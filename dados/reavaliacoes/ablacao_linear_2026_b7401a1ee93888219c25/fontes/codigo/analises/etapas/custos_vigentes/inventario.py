"""Inventário das carteiras primárias, distinguindo publicações de cópias e controles."""
from pathlib import Path
import os
from infraestrutura.artefatos import RAIZ, ler_json, sha256

def arquivos(pasta, nome):
    for base, dirs, nomes in os.walk(pasta):
        dirs[:] = [n for n in dirs if n not in ('fontes', 'checkpoints', '__pycache__')]
        if nome in nomes: yield Path(base)/nome


def montar():
    jobs = []; fontes = {}; exclusoes = []; raiz = RAIZ/'dados/experimentos'
    for p in sorted(raiz.iterdir()):
        if not p.is_dir() or not (p/'congelamento.json').exists(): continue
        nome = p.name; f = ler_json(p/'congelamento.json')
        fontes[(p/'congelamento.json').relative_to(RAIZ).as_posix()] = sha256(p/'congelamento.json')
        if nome.startswith(('retorno24_', 'penalizacao_', 'normalizacao_')):
            analises = RAIZ/'registros/analises/1e7c5ed662fba55ddd25' if nome.startswith('retorno24_') else p/'analises'
            for fase in ('desenvolvimento','avaliacao'):
                for q in sorted((analises/fase/'operacoes').glob('*.json')):
                    obj=ler_json(q)
                    if isinstance(obj,dict) and isinstance(obj.get('estrategia'),dict) and 'ordens' in obj:
                        jobs.append({'tipo':'spot24_preliminar','pai':nome,'fonte':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q),'cenario':'agravado' if 'agravado' in q.name else 'base'})
            continue
        if nome.startswith(('alvo_retorno_diario_', 'cryptomamba_diario_', 'ohlcv24_')):
            exclusoes.append({'execucao': nome, 'motivo': 'Preparacao/interrupcao sem publicacao operacional completa.'}); continue
        if nome.startswith(('operacional_futuros_', 'historico_treino_')):
            for q in sorted(arquivos(p, 'resultado.json')):
                if 'fontes' in q.parts or not (q.parent/'curva.npz').exists(): continue
                jobs.append({'tipo':'operacional', 'pai':nome, 'fonte':q.relative_to(RAIZ).as_posix(), 'sha256':sha256(q)})
            continue
        if nome.startswith(('futuros_', 'smart_mercados_', 'revisao_operacional_')):
            ct = f['assinatura']
            for g in ct['grade']:
                pasta = p/'carteiras'/g['chave']
                fontes_resumo = [pasta/n for n in ('resumo.json','resultado.json') if (pasta/n).exists()]
                if not fontes_resumo: raise ValueError(f'Carteira esperada ausente: {pasta}')
                q = fontes_resumo[0]
                jobs.append({'tipo':'retida' if nome.startswith(('smart_','revisao_')) else 'futuro24', 'pai':nome, 'fonte':q.relative_to(RAIZ).as_posix(), 'sha256':sha256(q), 'grade':g})
            continue
        for q in sorted(arquivos(p, 'operacoes_base.json')):
            if 'fontes' in q.parts: continue
            for cenario in ('base','agravado'):
                arq = q.with_name(f'operacoes_{cenario}.json')
                if arq.exists():jobs.append({'tipo':'spot24', 'pai':nome, 'fonte':arq.relative_to(RAIZ).as_posix(), 'sha256':sha256(arq), 'cenario':cenario})
        for q in sorted(arquivos(p, 'sinais.json')):
            if 'fontes' in q.parts or not (q.parent/'resumo.json').exists(): continue
            resumo = ler_json(q.parent/'resumo.json')
            if isinstance(resumo,dict) and 'dias_decisao' in resumo and 'politica' in resumo:
                jobs.append({'tipo':'spot_retida','pai':nome,'fonte':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q), 'resumo':(q.parent/'resumo.json').relative_to(RAIZ).as_posix()})
        pubs = [p/'publicacao/carteiras.json']
        if nome.startswith('generalizacao_moedas_'):pubs = [p/s/'publicacao/carteiras.json' for s in ('ETHUSDT','BNBUSDT')]+[p/'XRPUSDT/continuacao_001/publicacao/carteiras.json']
        for q in pubs:
            if not q.exists():continue
            for linha in ler_json(q):
                fonte = RAIZ/linha['pasta']/'resultado.json'
                jobs.append({'tipo':'diaria','pai':nome,'fonte':fonte.relative_to(RAIZ).as_posix(),'sha256':sha256(fonte),'registro':linha,'base':q.parent.parent.relative_to(RAIZ).as_posix()})
    chaves = [j['fonte'] for j in jobs]
    assert len(chaves) == len(set(chaves)), 'Carteiras duplicadas no inventario'
    return {'jobs':jobs,'fontes_congelamento':fontes,'exclusoes':exclusoes}
