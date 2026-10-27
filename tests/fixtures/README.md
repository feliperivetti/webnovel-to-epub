# HTML fixtures

As fixtures de Panda/NovelPhoenix, CentralNovel e NovelsBr foram recapturadas
em **27/10/2026**, a partir das seis URLs indicadas pelo usuário. Todas
responderam HTTP 200 com os metadados ou o conteúdo do capítulo esperado.
Os testes leem os arquivos localmente e não precisam consultar os sites.

Os três fluxos completos usam os valores já preenchidos de **`expected.json`**.
Confira as expectativas no HTML original ao alterar as fixtures. Consulte o
[guia de execução e preenchimento](../../docs/offline-tests.md).

| Fonte | Página principal | Capítulo |
| --- | --- | --- |
| Panda/NovelPhoenix | [Shadow Slave](https://novelphoenix.com/novel/shadow-slave) | [Capítulo 1](https://novelphoenix.com/novel/shadow-slave/chapter-1) |
| CentralNovel | [Shadow Slave](https://centralnovel.com/series/shadow-slave-20260913/) | [Capítulo 1](https://centralnovel.com/shadow-slave-capitulo-1/) |
| NovelsBr | [Escravo das Sombras](https://novels-br.com/novels/escravo-das-sombras) | [Capítulo 1](https://novels-br.com/novels/escravo-das-sombras/volume-unico-capitulo-1--o-pesadelo-comeca) |

## Origem e redução

`sources.json` registra a URL solicitada/final, data UTC, status, título, tamanho
e SHA-256 de cada captura completa, além do SHA-256 e da seleção de conteúdo
da fixture reduzida. Os HTMLs completos e o manifesto original estão em
`outputs/diagnostics/fixture-captures-20261027/` na cópia local, ignorados pelo Git.
As fixtures reduzidas são versionadas junto com os testes.

A redução preserva elementos, atributos, hierarquia, acentos e trechos reais.
Remove a maior parte da página sem relação com o parser, scripts e estilos.
Os capítulos contêm apenas os primeiros três parágrafos da história. Não são
cópias completas do capítulo e não devem ser usados para medir seu tamanho real.

- **Panda:** header, autor, capa, estatísticas e sinopse do NovelPhoenix; título
  e três parágrafos do capítulo. O índice desse scraper é gerado por URL, sem
  extração de uma lista de links. NovelPhoenix também está registrado como
  alias desse scraper, e o fluxo completo usa a URL indicada na captura.
- **CentralNovel:** bloco `bigcontent`, sinopse e as linhas reais dos capítulos
  3, 2 e 1, na ordem do site. Cada linha mantém tanto o link de leitura quanto
  o link de PDF. O capítulo preserva o aviso real `Traduzido usando o ChatGPT`.
- **NovelsBr:** bloco `#hero-novel`, sinopse e as três primeiras linhas do índice,
  com a hierarquia do accordion. O capítulo preserva os dois títulos existentes
  e as atribuições/links ocultos que o parser precisa remover.

Os contadores exibidos nos metadados continuam sendo os da captura completa
(por exemplo, milhares de capítulos). Eles não foram reescritos para coincidir
com o índice reduzido. Nos testes de limite, o disponível é o número de linhas
mantidas na fixture, não esse contador visual.

## Expectativas conferidas

| Fonte | Título da novel | Autor | Título extraído do capítulo |
| --- | --- | --- | --- |
| Panda | Shadow Slave | Guiltythree | Chapter 1 - 1: Nightmare Begins |
| CentralNovel | Shadow Slave | Guiltythree | O Pesadelo Começa |
| NovelsBr | Escravo das Sombras | Guiltythree | Capítulo 1: O Pesadelo Começa |

O parser da CentralNovel extrai o autor do link `/writer/`, sem incluir o rótulo
`Autor:`. Se o nome vier sem link, usa o campo identificado por esse rótulo e
remove somente o prefixo. A fixture mantém o `<b>` e o `<a>` reais desse campo.

## Regressões reveladas pelas páginas reais e corrigidas

1. **Limite de capítulos na CentralNovel:** o parser contava os links de PDF
   como capítulos. Agora conta apenas os links de leitura nas linhas do índice,
   excluindo controles e caminhos de PDF. Com três capítulos e três PDFs na
   fixture, um pedido de cinco capítulos retorna somente três. O teste deixou
   de ser `xfail` e também verifica outros valores de início e um índice só de PDFs.
2. **Avisos de tradução da CentralNovel:** por decisão do usuário, o conteúdo
   é preservado, incluindo `Inteligência Artificial` e `Traduzido usando o
   ChatGPT`. A limpeza desses avisos foi removida. Os testes verificam que o
   primeiro parágrafo e a história seguinte permanecem no resultado.

As fixtures antigas do RoyalRoad permanecem independentes desta atualização.
