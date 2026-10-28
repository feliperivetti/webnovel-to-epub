# WebNovel to EPUB

API em Python/FastAPI para buscar webnovels, baixar capítulos e montar arquivos
EPUB. A geração acontece em segundo plano, com acompanhamento por Server-Sent
Events (SSE) e download separado do arquivo final.

## Começar a desenvolver

Use **Python 3.11** como referência, a mesma versão do CI e da imagem Docker.
Execute os comandos na raiz do repositório.

No PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m uvicorn src.main:app --reload
```

No Linux/macOS, ative o ambiente com `source venv/bin/activate` e copie a
configuração com `cp .env.example .env`. Os demais comandos são os mesmos.
Se o PowerShell impedir a ativação, use `.\venv\Scripts\python.exe` no lugar
de `python`, sem mudar a política de execução.

A API fica em `http://127.0.0.1:8000`; abra `/docs` para explorar os endpoints
e `/` para verificar o estado do serviço. Sem `API_JWT_SECRET`, a autenticação
é dispensada no desenvolvimento local. Configure esse segredo no ambiente de
publicação antes de expor as rotas de geração.

Para testar JWT localmente sem gerar tokens no terminal, configure
`API_JWT_SECRET` e `DEBUG=true`, reinicie a API e use `POST /dev/token` no
`/docs`. Cole o `access_token` retornado em **Authorize**. Esse helper só aceita
acesso local e não é registrado com `DEBUG=false`; veja o [passo a passo](docs/api.md#gerar-um-token-pelo-swagger-local).

## Fontes implementadas

| Fonte | Identificador da busca | Domínios registrados para geração |
| --- | --- | --- |
| RoyalRoad | `royal` | `royalroad.com` |
| PandaNovel / NovelFire / NovelPhoenix | `panda` | `pandanovel.co`, `novelfire.net`, `novelphoenix.com` |
| CentralNovel | `central` | `centralnovel.com` |
| NovelsBr | `novelsbr` | `novels-br.com` |

O scraper Panda gera os links de capítulos em `novelphoenix.com`; sua busca
ainda consulta o endpoint do PandaNovel. As fontes dependem dos layouts e das
restrições dos sites externos. Ter um parser e testes offline não garante que
uma consulta online esteja disponível; consulte o guia de diagnóstico quando
um site mudar ou apresentar uma proteção antibot.

## Fluxo da API

1. `GET /search/?source=...&query=...` busca novels em uma fonte.
2. `POST /books/generate?url=...&qty=...&start=...` aceita uma geração e retorna
   `202`, com `task_id` e `status_url`.
3. `GET /books/events/{task_id}` transmite status e percentual por SSE.
4. `GET /books/download/{task_id}` entrega o EPUB pronto e agenda a remoção do
   arquivo e da tarefa após o envio.

As rotas `/books` usam `Authorization: Bearer <JWT>` quando o segredo está
configurado. Veja exemplos, autenticação e limites em [API](docs/api.md).

## Organização

```text
src/                    Aplicação executada pela API
  classes/              Scrapers: HTML e download de capítulos
  routes/               Endpoints de busca, geração, eventos e download
  schemas/              Modelos de dados e respostas
  services/             Busca por fonte, registry, tarefas, EPUB e métricas
  utils/                Logger, exceções e textos/templates compartilhados
tests/                  Testes automatizados e helpers de teste
  fixtures/             HTMLs de referência, origem e valores esperados
scripts/                Diagnóstico e benchmarks executados manualmente
docs/                   Guias para desenvolvimento e operação
outputs/                Logs, diagnósticos e métricas locais; fora do Git
.github/workflows/      Verificações automáticas no GitHub
.agent/skills/          Instruções auxiliares para assistentes de desenvolvimento
```

## Comandos frequentes

Com o ambiente virtual ativo:

```powershell
# Verificar o código e executar os testes offline
python -m ruff check .
python -X utf8 -m pytest

# Inspecionar um scraper sem iniciar a API
python -m scripts.debug_scraper --help

# Ler métricas já registradas, sem acessar os sites
python -m scripts.benchmark_viewer
```

O GitHub Actions instala `requirements-dev.txt` e executa Ruff e pytest em
pushes e pull requests para `main`. Playwright é opcional e só é necessário
para o diagnóstico com navegador, explicado no guia específico.

## Documentação

| Guia | Conteúdo |
| --- | --- |
| [Desenvolvimento](docs/development.md) | Configuração, dependências, arquitetura, extensão dos scrapers e ferramentas |
| [API](docs/api.md) | Exemplos HTTP, JWT, progresso, download e limites atuais |
| [Testes offline](docs/offline-tests.md) | Executar testes, conferir EPUBs e manter fixtures/expectativas |
| [Diagnóstico dos scrapers](docs/scraper-debugging.md) | Investigar HTTP, seletores, proxies e páginas com JavaScript |
| [Roadmap](docs/roadmap.md) | Ideias futuras, sem compromisso de implementação |

## Docker

```powershell
docker build -t webnovel-to-epub .
docker run --rm -p 8000:8000 --env-file .env webnovel-to-epub
```

A imagem instala somente as dependências da aplicação e copia `src/`.
Testes, ferramentas manuais e credenciais locais não entram na imagem.
O serviço usa atualmente um único processo e mantém as tarefas na memória;
reiniciar o container interrompe as gerações em andamento. Os EPUBs ficam no
diretório temporário do sistema; logs e métricas ficam em `outputs/`.
