"""HTTP público GET com recibos, timeout e respeito a Retry-After; sem credenciais."""
import hashlib
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from infraestrutura.artefatos import agora, salvar_json


class ClienteHTTP:
    def __init__(self, pasta, abrir=urlopen, esperar=time.sleep, tentativas=3, espera_maxima=60):
        self.pasta = pasta
        self.pasta.mkdir(parents=True,exist_ok=True)
        self.abrir,self.esperar = abrir,esperar
        self.tentativas,self.espera_maxima = tentativas,espera_maxima
        self.chamadas = 0

    def obter(self,url):
        u = urlparse(url)
        permitido = (u.hostname=='data.binance.vision' and u.path.startswith('/data/spot/monthly/klines/')) or (
            u.hostname=='data-api.binance.vision' and u.path in ('/api/v3/klines','/api/v3/time'))
        if u.scheme!='https' or not permitido or u.username or u.password or u.port:
            raise ValueError('Somente fontes públicas de mercado permitidas neste cliente.')
        self.chamadas += 1
        for tentativa in range(1,self.tentativas+1):
            self.esperar(.25)
            registro={'url':url,'metodo':'GET','inicio_utc':agora(),'tentativa':tentativa}
            caminho=self.pasta/f'{self.chamadas:06d}_{tentativa}.json'
            try:
                with self.abrir(Request(url,headers={'User-Agent':'CryptoCasting/dados-mercado-1','Accept':'*/*'}),timeout=30) as resposta:
                    corpo=resposta.read(128*1024*1024+1)
                    if len(corpo)>128*1024*1024:
                        raise ValueError('Resposta excede tamanho máximo.')
                    registro.update(status=resposta.status,headers=dict(resposta.headers),bytes=len(corpo),sha256=hashlib.sha256(corpo).hexdigest(),fim_utc=agora())
                salvar_json(caminho,registro)
                return corpo,registro
            except HTTPError as erro:
                registro.update(status=erro.code,headers=dict(erro.headers),erro=erro.read(4096).decode('utf-8',errors='replace'),fim_utc=agora())
                erro.close()
                salvar_json(caminho,registro)
                if erro.code==429:
                    valor=erro.headers.get('Retry-After')
                    try: espera=float(valor)
                    except (TypeError,ValueError):
                        raise RuntimeError('429 sem Retry-After numérico; coleta interrompida.') from erro
                    if not 0<=espera<=self.espera_maxima:
                        raise RuntimeError(f'429 exige espera de {valor}s; interrompido sem tentar outro endpoint.') from erro
                elif 500<=erro.code<600:
                    espera=2**(tentativa-1)
                else:
                    # Inclui 403/418/451: nunca insistir ou contornar bloqueio.
                    raise
                if tentativa==self.tentativas:
                    raise
                self.esperar(espera)
            except (URLError,TimeoutError,OSError) as erro:
                registro.update(erro=f'{type(erro).__name__}: {erro}',fim_utc=agora())
                salvar_json(caminho,registro)
                if tentativa==self.tentativas:
                    raise
                self.esperar(2**(tentativa-1))
            except Exception as erro:
                registro.update(erro=f'{type(erro).__name__}: {erro}',fim_utc=agora())
                salvar_json(caminho,registro)
                raise
