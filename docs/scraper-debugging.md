# Diagnosticar os scrapers pelo terminal

Execute os comandos na raiz do projeto, no PowerShell. Não é necessário iniciar
a API nem configurar JWT. Use o Python do ambiente virtual:

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper --help
```

O comando usa os métodos atuais do scraper selecionado pelo domínio da URL:
`get_book_metadata()`, `get_chapters_link()` e `get_chapter_content(url)`.
Ele não gera EPUB, não cria capítulos de erro e não registra benchmarks.
As chamadas são sequenciais, com um capítulo por padrão. As tentativas adicionais
de `_fetch_with_retry()` não são usadas; comportamentos internos de cada método,
como uma segunda tentativa após HTTP 429, continuam valendo.

## Verificar cada etapa

```powershell
$novel = "https://novelfire.net/book/shadow-slave"

# Título, autor, descrição e capa
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage metadata

# URLs que o scraper seleciona ou monta
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage links --qty 3

# Resolver os links e extrair apenas o primeiro capítulo
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage chapter --qty 1

# Todas as etapas, limitadas a um capítulo
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --qty 1
```

Para RoyalRoad, use uma URL de novel desse site no mesmo comando:

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper "https://www.royalroad.com/fiction/21220/mother-of-learning" --qty 1
```

`--start 5 --qty 2` testa os capítulos 5 e 6. Um teste de links bem-sucedido
**não confirma que o conteúdo pode ser baixado**: o scraper Panda/NovelFire
atual apenas constrói as URLs, sem consultar o índice.

## Testar uma URL de capítulo específica

Copie o endereço real de um capítulo aberto no navegador para comparar com o
endereço gerado pelo scraper:

```powershell
$chapter = "https://novelphoenix.com/novel/shadow-slave/chapter-1"
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage chapter --chapter-url $chapter --traceback
```

Isso ignora `get_chapters_link()`. `--stage fetch --chapter-url $chapter` verifica
somente a resposta HTTP e seus seletores, sem tentar extrair um capítulo.
Um `PASS` nessa etapa confirma a requisição HTTP; não valida o texto do capítulo.

Os links de capítulo do Panda/NovelFire agora usam
`https://novelphoenix.com/novel/<slug>/chapter-<numero>`. A URL principal da
novel continua sendo a do NovelFire, usada para os metadados e a seleção do
scraper. Na comparação de 27/10/2026, o novo domínio entregou o mesmo conteúdo
com `noti=1`, `noti=0` e sem parâmetro. `noti=1` acrescentou um script que abre o
aviso de boas-vindas no navegador; esse aviso não bloqueou a extração de
`div#content`. Por isso os links gerados omitem o parâmetro.

## Inspecionar os resultados

Cada execução cria uma pasta em `diagnostics/<data-hora>/`, ignorada pelo Git:

- `report.json`: resultado por etapa, erros, URLs solicitadas/finais,
  redirecionamentos, status HTTP, título da página e quantidade de ocorrências
  de cada seletor atual.
- `response-01.html`, etc.: corpo original de cada resposta, inclusive HTTP 403/404.
- `chapter-001.html` e `chapter-001.txt`: conteúdo extraído, quando houver texto.

Escolha uma pasta explícita com `--output-dir diagnostics/meu-teste`. Use uma
pasta diferente para cada comparação, para não confundir arquivos de execuções anteriores.
Erros de conexão sem resposta HTTP aparecem no relatório, sem um arquivo HTML.
O código de saída é `0` se todas as etapas selecionadas passarem, `1` se alguma
falhar e `2` para argumentos inválidos. No PowerShell, consulte `$LASTEXITCODE`.

Como interpretar:

| Resultado | O que investigar |
| --- | --- |
| HTTP 403/429 | Restrição de acesso ou limite de requisições. |
| HTTP 404 | URL incorreta, domínio antigo ou capítulo removido. |
| HTTP 200 + título `Loading...` + `chap_content: 0` | O HTML recebido não contém o capítulo esperado; pode ser uma página intermediária ou exigir JavaScript. |
| HTML contém a história, mas `chap_content: 0` | O seletor provavelmente precisa acompanhar o layout atual. |
| URL final ou domínio diferente | Redirecionamento ou endereço montado com domínio antigo. |
| Texto extraído e arquivo `.txt` correto | A extração desse capítulo funcionou; confira o arquivo antes de testar lotes. |

Abra o HTML salvo no editor para examinar o que o servidor realmente retornou.
O diagnóstico usa `cloudscraper` como o projeto; não executa JavaScript de navegador.
Marcadores de bloqueio são apenas pistas, não um diagnóstico definitivo.

## Comparar conexão direta e proxy

Por padrão, o comando mantém a configuração de proxy do scraper. Para ignorar
os proxies do `.env` e do sistema **somente nessa execução**:

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage chapter --direct --timeout 10
```

O comando não altera o `.env`. Cabeçalhos de autorização e cookies não são
incluídos no relatório; valores conhecidos de segredo e credenciais de proxy
são ocultados nas mensagens. O HTML salvo é o corpo original da resposta.

## Repetir o parser sobre HTML salvo, sem rede

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage chapter --html diagnostics/meu-teste/response-01.html --selector "div#content" --output-dir diagnostics/offline
```

`--html` usa o arquivo UTF-8 como resposta sintética HTTP 200 para testar apenas
o parser. O status original deve ser consultado no relatório da execução online.
Para HTML da página principal, use `--stage metadata` ou `--stage links`.
`--selector` conta ocorrências de um seletor CSS adicional; não substitui o
seletor usado pelo scraper. Você pode repetir a opção para comparar seletores.

Teste offline com uma fixture conhecida do projeto:

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper $novel --stage chapter --html src/tests/fixtures/pandanovel_chap.html
```

Se a fixture passa e o HTML real falha, a diferença está entre a resposta atual
do site e a estrutura que o parser espera.

## Chamar os métodos manualmente

### RoyalRoad: observar a página antibot em um navegador

O HTML `Making sure you're not a bot!` encontrado em 27/10/2026 contém o desafio
Anubis (`script#anubis_challenge`) e carrega JavaScript para um cálculo de prova
de trabalho. Não é necessário haver um CAPTCHA visual. `requests`/`cloudscraper`
não executam esse JavaScript, e aumentar `--timeout` ou chamar `sleep()` não
faz o HTML já recebido se transformar na página da novel.

Instale a dependência opcional no ambiente virtual:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-browser.txt
```

Abra o Edge com um contexto novo, sem os cookies do seu navegador pessoal:

```powershell
.\venv\Scripts\python.exe -m scripts.debug_scraper "https://www.royalroad.com/fiction/21220/mother-of-learning" --stage metadata --browser msedge --headed --pause --direct --wait-seconds 45
```

O comando abre uma janela, salva o HTML inicial e espera pelo seletor real do
RoyalRoad (`div.fic-header` ou `div.chapter-inner.chapter-content`), por até 45
segundos. Depois da espera, mantém a janela aberta até você pressionar Enter
**no terminal**. Observe a navegação ou abra o DevTools nessa janela para
inspecionar as requisições. O site pode liberar a página imediatamente, mostrar
Anubis ou outra proteção; o comando não garante reproduzir a mesma decisão do
servidor em todas as sessões.

Resultados adicionais na pasta do diagnóstico:

- `browser-01-initial.html`: DOM logo após a navegação; o JavaScript pode já
  ter executado alguma coisa antes desse snapshot.
- `browser-01-final.html` e `browser-01-final.png`: DOM e imagem após a espera.
- `report.json`, seção `browser.pages`: títulos inicial/final, URL final,
  tempo decorrido e se o seletor esperado apareceu.

O contexto é novo em cada execução e fica aberto durante todas as etapas dessa
execução. Valores de cookies não são exportados. Se o site exigir uma ação
manual, você pode realizá-la na janela visível. Se a página continuar bloqueada,
o diagnóstico registra a falha, sem tratar a página de proteção como capítulo.

Use `--browser chrome` para o Chrome instalado. `--browser chromium` exige a
instalação adicional do Chromium do Playwright (`python -m playwright install chromium`).
Sem `--headed`, o navegador roda em segundo plano; compare os modos, pois o
servidor pode responder de forma diferente. O modo de navegador é uma ferramenta
de diagnóstico sequencial: a API continua usando a sessão HTTP atual.

Para observar manualmente no seu navegador habitual, tente uma janela anônima
e abra o DevTools em **Network**, com **Preserve log**, antes de navegar. Se a
resposta já for a novel, o navegador não recebeu o desafio naquela consulta.
Cookies existentes, cabeçalhos, características do cliente e endereço de saída
podem explicar diferenças entre o navegador e o script. Não é preciso apagar
os dados da sua sessão pessoal. Abrir o HTML salvo como arquivo local não
reproduz a negociação com o servidor original.

Referências: [Anubis](https://github.com/TecharoHQ/anubis) e
[navegadores no Playwright](https://playwright.dev/python/docs/browsers).

### Métodos do scraper no interpretador Python

Abra o interpretador na raiz do projeto:

```powershell
.\venv\Scripts\python.exe
```

```python
from src.diagnostics import create_scraper

book = create_scraper("https://novelfire.net/book/shadow-slave", qty=1, start=1)
metadata = book.get_book_metadata()
print(metadata)
links = book.get_chapters_link()
print(links)
chapter = book.get_chapter_content(links[0])
print(chapter.title)
print(len(chapter.content), chapter.content[:500])
book._session.close()
```

Essas chamadas manuais podem retornar conteúdo vazio ou lançar exceções,
conforme o scraper. O comando de diagnóstico acrescenta validação de texto e
salvamento de evidências. O fluxo normal `scrape_novel()` atualmente captura
falhas individuais e insere `Error Chapter` no EPUB; por isso a conclusão da
tarefa na API não garante que os capítulos foram extraídos.

Para acompanhar os logs da API em outro terminal:

```powershell
Get-Content .\logs\app.log -Tail 80 -Wait
```
