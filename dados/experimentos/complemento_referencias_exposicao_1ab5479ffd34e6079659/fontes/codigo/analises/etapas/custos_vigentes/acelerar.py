"""Cache apenas da conversão de timestamps escalares repetidos nas curvas."""
from functools import lru_cache
import pandas as pd


def instalar():
    original=pd.to_datetime
    @lru_cache(maxsize=150000)
    def instante(valor,utc):return original(valor,unit='m',utc=utc)
    def converter(arg,*args,**kwargs):
        if type(arg) is int and not args and set(kwargs).issubset({'unit','utc'}) and kwargs.get('unit')=='m':
            return instante(arg,kwargs.get('utc',False))
        return original(arg,*args,**kwargs)
    pd.to_datetime=converter
    return instante


if __name__=='__main__':
    instalar()
    from .executar import executar
    executar()
