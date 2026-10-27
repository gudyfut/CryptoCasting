"""Verifica a cobertura neural de um bloco, sem declarar sua fase concluída."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,verificar_arquivos,sha256,identidade,agora
from previsao24.configuracao import celulas

def verificar(fold):
    ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
    pasta=RAIZ/ponteiro['caminho']
    execucao=ler_json(pasta/'execucao.json')
    c=execucao['assinatura']['configuracao']
    fase='desenvolvimento' if fold in c['folds_desenvolvimento'] else 'avaliacao'
    esperadas={identidade(x)[:20]:x for x in celulas(c,fase) if x['fold']==fold}
    if not esperadas:
        raise ValueError('Bloco desconhecido.')
    encontradas={}
    recibos={}
    for p in pasta.glob('celulas/*/tentativa_*/tentativa.json'):
        t=ler_json(p)
        x=t['celula']
        if x['fold']!=fold or x['modelo'] not in ('lstm','mamba') or t['status']!='auditada':
            continue
        chave=identidade(x)[:20]
        if chave in encontradas:
            raise ValueError('Duplicação de resultados auditados.')
        if p.parent.parent.name!=chave:
            raise ValueError('Identidade da célula incorreta.')
        auditoria=ler_json(p.parent/'auditoria.json')
        if auditoria['status']!='aprovado' or auditoria['celula']!=x:
            raise ValueError('Recibo incompatível.')
        verificar_arquivos(p.parent,auditoria['arquivos'])
        encontradas[chave]=x
        recibos[p.parent.relative_to(RAIZ).as_posix()]=sha256(p.parent/'auditoria.json')
    if encontradas!=esperadas:
        raise ValueError(f'Bloco neural incompleto: {len(encontradas)}/{len(esperadas)}')
    registro={'status':'cobertura_neural_verificada','execucao':ponteiro['id'],'bloco':fold,'utc':agora(),
              'ajustes':len(encontradas),'auditorias':recibos,'verificador_sha256':sha256(Path(__file__)),
              'limite':'Confere cobertura e integridade dos ajustes neurais. Não atesta conclusão das referências, consolidação ou avaliação final.'}
    salvar_json(RAIZ/'registros/auditorias'/ponteiro['id']/f'{fold}_neurais.json',registro)
    print(f'{fold}: {len(encontradas)} ajustes neurais com cobertura e hashes verificados.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--bloco',required=True)
    verificar(parser.parse_args().bloco)
