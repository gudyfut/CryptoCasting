"""Revisão compatível do leitor; base congelada e tentativa inicial preservadas."""
import argparse
import io
import unittest
from pathlib import Path
from infraestrutura.artefatos import RAIZ,salvar_json,sha256,agora
from backtest_carteira import ciclo
from backtest_carteira.mercado import carregar

if __name__=='__main__':
    registro=ciclo.REG/'revisao_loader';original_fontes=ciclo.fontes_atuais;original_entradas=ciclo.entradas
    def fontes():
        fs=original_fontes();fs['run_backtest_revisado.py']=sha256(RAIZ/'run_backtest_revisado.py');return fs
    def entradas(cfg):
        ins,guard,mu,partes=original_entradas(cfg);arq=registro/'qualificacao_loader.json';ins[arq.relative_to(RAIZ).as_posix()]=sha256(arq);return ins,guard,mu,partes
    ciclo.REG=registro;ciclo.carregar_mercado=carregar;ciclo.fontes_atuais=fontes;ciclo.entradas=entradas
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='acao',required=True);s.add_parser('preparar');q=s.add_parser('executar');q.add_argument('--autorizacao',required=True,type=Path);a=p.parse_args()
    if a.acao=='preparar':
        if (registro/'qualificacao_loader.json').exists():raise FileExistsError('Qualificação já existe; preservar.')
        log=io.StringIO();r=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('tests_backtest_carteira.test_mercado'));registro.mkdir(parents=True,exist_ok=True);(registro/'qualificacao_loader.log').write_text(log.getvalue(),encoding='utf-8')
        salvar_json(registro/'qualificacao_loader.json',{'utc':agora(),'status':'aprovado' if r.wasSuccessful() and not r.skipped else 'reprovado','testes':r.testsRun,'fontes':fontes(),'simulacoes_mercado':0})
        if not r.wasSuccessful() or r.skipped:raise ValueError('Leitor reprovado.')
        print(ciclo.preparar())
    else:ciclo.executar(a.autorizacao)
