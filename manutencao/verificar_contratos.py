"""Executa testes e grava um recibo vinculado às fontes realmente testadas."""
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,fontes,sha256,salvar_json,agora

assinatura=fontes()
assinatura.update({p.relative_to(RAIZ).as_posix():sha256(p) for p in sorted((RAIZ/'tests').glob('test_*.py'))})
resultado=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=RAIZ,capture_output=True,text=True)
print(resultado.stdout+resultado.stderr,flush=True)
registro={'status':'aprovado' if resultado.returncode==0 else 'falha','utc':agora(),'fontes':assinatura,
          'comando':'python -m unittest discover -s tests -v','saida':resultado.stdout+resultado.stderr,'codigo_saida':resultado.returncode}
salvar_json(RAIZ/'registros/qualificacao/testes_atual.json',registro)
sys.exit(resultado.returncode)
