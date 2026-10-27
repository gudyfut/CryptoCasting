# Ambiente científico qualificado

Inspecionado e qualificado em 18/10/2026: WSL Ubuntu, Python 3.12.13, NVIDIA RTX 4050 Laptop com 6 GB. Interpretador utilizado: `~/.venvs/cc/bin/python`. O Python do Windows é outro ambiente e não deve ser confundido com este.

| Componente | Versão utilizada |
|---|---|
| PyTorch | 2.6.0+cu118 |
| Mamba oficial | 2.2.6.post3 |
| causal-conv1d | 1.6.2.post1 |
| Transformers | 4.51.3 |
| Triton | 3.2.0 |
| NumPy | 2.2.6 |
| pandas | 3.0.3 |
| PyArrow | 24.0.0 |
| Numba | 0.61.2 |

Os wheels instalados de Mamba e causal-conv1d são Linux x86_64, CPython 3.12, CUDA 11, PyTorch 2.6 e ABI C++ antiga (`cxx11abiFALSE`). A compatibilidade foi verificada nesta máquina; não basta instalar versões de nomes parecidos em outro ambiente.

Proveniência registrada em [proveniencia_cuda_2026-10-18.json](../historico/qualificacoes/proveniencia_cuda_2026-10-18.json): URLs oficiais, hashes dos wheels registrados pelo instalador e hashes dos módulos CUDA compilados. As qualificações `ambiente_*.json` incluem versões completas, fontes e comparações numéricas. Cada tentativa científica também guarda sua cópia do ambiente.

Fontes dos wheels: [Mamba 2.2.6.post3](https://github.com/state-spaces/mamba/releases/tag/v2.2.6.post3) e [causal-conv1d 1.6.2.post1](https://github.com/Dao-AILab/causal-conv1d/releases/tag/v1.6.2.post1).

`requirements.txt` fixa parte das bibliotecas, mas sozinho não instala os kernels compatíveis. Para reconstruir em outra máquina, criar um ambiente separado, instalar o PyTorch correspondente, obter os wheels compatíveis e conferir os hashes registrados. Executar `pip check`, os testes sintéticos e `run_barreiras.py qualificar` antes de usar esse ambiente em ciência. Essa reconstrução limpa em outra máquina ainda não foi executada.

O treino usa float32, sem AMP e sem TF32. O teste comparativo do scan usa tolerância numérica declarada; o teste de causalidade exige igualdade do prefixo. A recarga do mesmo checkpoint reproduziu exatamente as probabilidades. Treinos distintos do Mamba podem variar em poucos ULPs pelas reduções dos kernels: seed fixa não é promessa de igualdade bit a bit em qualquer hardware.

Durante o ciclo inicial, auditorias de artefatos, consolidações e tarefas do painel ocorreram em paralelo na mesma máquina. Os tempos registrados refletem essa carga variável e não constituem um benchmark controlado de velocidade. Preservar os valores originais com essa condição explícita; não normalizar os tempos retrospectivamente. Registro: [condições de execução](../historico/qualificacoes/condicoes_execucao_4e232a796fcda0ea34c3.json).

Não atualizar bibliotecas durante uma grade em execução. Uma mudança de código, configuração ou ambiente exige outra identidade. O fallback PyTorch permanece no código para investigação e testes sintéticos; este contrato não permite usá-lo como substituto silencioso do backend oficial nem tratá-lo como a mesma execução.
