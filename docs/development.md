# Desenvolvimento

## Ambiente e dependências

Siga a instalação do [README](../README.md). As listas têm papéis separados:

| Arquivo | Quando instalar |
| --- | --- |
| `requirements.txt` | Para executar a API ou os scrapers |
| `requirements-dev.txt` | Para desenvolver; inclui a aplicação, pytest, seus plugins, HTTPX e Ruff |
| `requirements-browser.txt` | Opcional: Playwright para diagnóstico com navegador |

As versões diretas estão fixadas. Ao adicionar uma biblioteca, escolha a lista
correspondente e confira testes/Ruff. Não é necessário instalar Playwright para
rodar a API ou os testes offline. `pyproject.toml` centraliza a configuração de
pytest e Ruff; não há etapa de empacotamento ou instalação com `pip install .`.

## Configuração

Copie `.env.example` para `.env` e mantenha credenciais somente no arquivo local
ou no ambiente de execução. O `.env` não é versionado nem copiado para Docker.
Execute a aplicação e as ferramentas a partir da raiz do repositório.

| Variável | Padrão | Uso |
| --- | --- | --- |
| `APP_NAME` | `Novel Scraper API` | Nome apresentado pela API |
| `DEBUG` | `false` | Imprime o tempo das requisições no terminal |
| `API_JWT_SECRET` | vazio | Segredo HS256; vazio dispensa validação no desenvolvimento |
| `MAX_CHAPTERS_LIMIT` | `1000` | Limite de `qty` na rota de geração |
| `DEFAULT_TIMEOUT` | `15` | Timeout usado pela base e pelo scraper RoyalRoad; outros scrapers também têm valores locais de 10/15 s |
| `MAX_WORKERS` | `2` | Downloads paralelos por geração |
| `PROXY_URL` | vazio | Proxy principal |
| `PROXY_URL_FALLBACK` | vazio | Proxy alternativo no tratamento de falhas do scraper |

`src/config.py` usa `pydantic-settings` e mantém uma instância de configuração
em cache. Reinicie o servidor ao alterar o `.env`. Os serviços de busca também
carregam o proxy por `python-dotenv`/variáveis de ambiente.

## Caminho de uma geração

1. `src/main.py` monta a API, CORS, autenticação e o agendamento da limpeza.
2. `src/routes/book_routes.py` valida a solicitação, cria a tarefa e devolve
   `202`. A busca fica em `src/routes/search_routes.py`.
3. `src/services/registry.py` encontra o serviço registrado para a URL. Os
   decorators dos serviços são carregados na inicialização da aplicação.
4. O serviço cria um scraper de `src/classes/`. `BaseScraper` coordena
   metadados, seleção de capítulos, tentativas, download paralelo e progresso.
   Cada subclasse implementa as particularidades de HTML da fonte.
5. `EpubBuilder` recebe o modelo `Novel`, definido em `src/schemas/`, e monta
   o EPUB. A rota salva um arquivo temporário e marca a tarefa como concluída.
6. `TaskManager` fornece o estado ao SSE e o caminho ao download. Após o envio,
   a tarefa e o arquivo são removidos.

Uma falha em todos os capítulos impede a geração. Falhas parciais resultam em
páginas de aviso no lugar dos capítulos afetados. Uma tarefa concluída, por si
só, não significa que todos os capítulos foram baixados com sucesso.

Os módulos em `src/utils/` concentram exceções, logger e textos/templates.
`MetricsService` registra o resultado do scraping; a métrica não mede a
montagem final do EPUB. `cleanup_service.py` verifica arquivos `.epub` antigos
no temporário do sistema a cada hora, com idade mínima de uma hora.

## Onde ficam os arquivos gerados

| Caminho | Conteúdo |
| --- | --- |
| `outputs/logs/app.log` | Log da aplicação, com rotação de 5 MB e três backups |
| `outputs/benchmarks.jsonl` | Uma métrica de scraping por linha JSON |
| `outputs/diagnostics/<data-hora>/` | Relatório, HTMLs e textos de uma execução de diagnóstico |
| `outputs/.cache/` | Caches de pytest e Ruff |
| `outputs/experiments/` | Experimentos locais antigos, preservados fora do código versionado |
| Temporário do sistema | EPUBs aguardando download; testes podem redirecioná-los |

`outputs/` é criado conforme necessário e ignorado por Git, Ruff e Docker.
Os diretórios de testes temporários também podem ficar ali, usando uma pasta
exclusiva por execução. HTMLs brutos de diagnóstico podem conter dados da
resposta do site; revise os arquivos antes de compartilhá-los.

Na reorganização, os arquivos locais antigos de `logs/`, `diagnostics/` e o
histórico de `benchmarks.jsonl` foram preservados sob `outputs/`. Um log aberto
por outro processo pode permanecer também no caminho antigo; a cópia histórica
está em `outputs/logs/`. As versões antigas desses caminhos continuam ignoradas
para evitar commits acidentais.

## Ferramentas manuais

Execute módulos a partir da raiz, com o ambiente virtual ativo:

```powershell
python -m scripts.debug_scraper --help
python -m scripts.benchmark_viewer
```

O primeiro investiga uma fonte por etapa, sem montar EPUB; veja o
[guia de diagnóstico](scraper-debugging.md). O segundo lê as métricas existentes
e mostra as últimas vinte execuções e um resumo no terminal.

O benchmark manual acessa sites reais e pode demorar:

```powershell
python -m scripts.run_benchmarks
```

Revise `TEST_URLS`, `TEST_QUANTITIES` e `TEST_CONFIGS` em
`scripts/run_benchmarks.py` antes de executar. Por padrão, compara lotes de
10/100 capítulos e configurações direta/proxies disponíveis. Ele chama o
scraper, sem montar EPUB. Não é teste de carga concorrente da API.
As gerações normais também gravam métricas, então o histórico pode misturar
execuções manuais e da aplicação; páginas de aviso contam no total do EPUB.

## Alterar ou adicionar uma fonte

1. Implemente ou ajuste a subclasse de `BaseScraper` em `src/classes/`:
   `get_book_metadata()`, `get_chapters_link()` e `get_chapter_content(url)`.
   Preserve os modelos de retorno definidos em `src/schemas/novel_schema.py`.
2. Implemente o serviço em `src/services/`, herdando de `BaseService`.
   Registre os domínios com `@ScraperRegistry.register(...)` e implemente
   `search()` e `get_book_instance()`.
3. Para disponibilizar a fonte na busca, inclua seu identificador no mapa
   `providers` de `src/routes/search_routes.py`.
4. Adicione HTMLs mínimos representativos em `tests/fixtures/`, registrando
   a origem, e testes para o comportamento alterado. Se incluir um fluxo
   completo offline, ajuste também `tests/offline_flow.py` e `expected.json`.
5. Execute Ruff e os testes, e atualize a tabela de fontes no README.

Use o diagnóstico com uma pequena quantidade de capítulos para confirmar o
HTML real antes de executar lotes. O exemplo de uma proteção antibot não deve
ser tratado como capítulo nem como prova de mudança de layout.

## Qualidade e automação

```powershell
python -m ruff check .
python -X utf8 -m pytest
```

O CI repete essas verificações em Python 3.11. Ruff usa suas regras padrão,
com exclusão de saídas geradas, instruções de agentes e experimentos locais;
não há formatação automática no workflow. Pytest coleta somente `tests/`.
Configure seu editor para pytest, caso a configuração local ainda use unittest.
Veja [Testes offline](offline-tests.md) para selecionar cenários e inspecionar
os EPUBs produzidos.

`.agent/skills/` contém instruções opcionais de apoio aos assistentes de
desenvolvimento. Não é importado pela aplicação e não entra na imagem Docker.
Experimentos locais não versionados podem continuar em `tinkering/`; código
reutilizável deve ir para `src/`, `scripts/` ou `tests/`, conforme sua função.
