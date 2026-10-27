# Roadmap

Ideias para avaliar quando houver uma necessidade concreta. Esta lista não
configura funcionalidades nem estabelece um compromisso de implementação.
Para instalar ou trabalhar no projeto, consulte o [README](../README.md) e o
[guia de desenvolvimento](development.md).

## Melhorias possíveis

| Ideia | Quando considerar | Apoio existente |
| --- | --- | --- |
| Consolidar medições de desempenho | Quando for necessário comparar fontes, proxies ou tamanhos de lote | `scripts/run_benchmarks.py`, `scripts/benchmark_viewer.py` e métricas em `outputs/benchmarks.jsonl` |
| Limitar requisições por domínio | Se bloqueios por excesso de requisições se tornarem recorrentes | Paralelismo configurável e tentativas com espera já existem; não há limitador global |
| Cachear metadados e índices | Quando consultas repetidas causarem custo ou latência relevantes | Ainda não implementado; Redis era uma opção levantada |
| Expor detalhes de uma novel | Quando o frontend precisar de uma consulta dedicada de sinopse, autor e status | A extração de metadados existe dentro dos scrapers |
| Avaliar outras técnicas de extração | Se mudanças de HTML tornarem os parsers atuais insuficientes | Diagnóstico HTTP e navegador opcional para investigar a causa |

## Estrutura atual

A API mantém gerações em segundo plano no mesmo processo, tarefas em memória
e progresso por SSE. Esse modelo continua adequado ao escopo pequeno atual.
Persistência de tarefas, fila externa e múltiplas instâncias podem ser avaliadas
se reinícios ou volume de uso justificarem a complexidade adicional.

O [guia da API](api.md) descreve os limites efetivamente implementados. Ideias
neste arquivo não devem ser documentadas como funcionalidades disponíveis.
