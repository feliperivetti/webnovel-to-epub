# Fluxos completos offline e expectativas manuais

## Onde preencher

Edite **`src/tests/fixtures/expected.json`**. Há um bloco independente para
`panda`, `centralnovel` e `novelsbr`. Todos os valores esperados começam como
`__PREENCHER__` ou `null`; nenhum foi extraído automaticamente pelo scraper.
Você pode preencher e validar uma fonte por vez.

Confira cada valor nos HTMLs `*_toc.html` e `*_chap.html` da mesma pasta, usando
as URLs e notas de `README.md`/`sources.json` como referência. As fixtures de
capítulo contêm apenas três parágrafos da história, não o capítulo completo.
Escolha trechos que estejam realmente nessas amostras.

| Campo | Como preencher |
| --- | --- |
| `book_title` | Título esperado do livro, como string. Comparação exata. |
| `author` | Autor esperado no EPUB, como string. Comparação exata. |
| `description_contains` | Lista de trechos que a descrição deve conter. Pode ser `[]` para não exigir trechos específicos. |
| `chapter_count` | Número inteiro, sem aspas. Os fluxos atuais solicitam um capítulo. |
| `has_cover` | Booleano JSON `true` ou `false`, sem aspas. |
| `chapters` | Lista na ordem esperada de leitura, com um objeto por capítulo. Os fluxos atuais exercitam o capítulo 1. |
| `chapters[].title` | Título esperado do capítulo, como string. Comparação exata. |
| `chapters[].required_text` | Lista com pelo menos um trecho do texto que deve estar presente. Inclua acentos e avisos que deseja preservar. |
| `chapters[].forbidden_text` | Lista de trechos que não devem aparecer. Use `[]` se não houver restrições adicionais. |

Substitua todos os placeholders do bloco preenchido, inclusive os `null`.
Use listas `[]`, não `null`, para campos opcionais de trechos. Os títulos e o
autor são comparados exatamente; nos trechos de texto e descrição, apenas
espaços/quebras de linha são normalizados. Maiúsculas, acentos e palavras
continuam sendo significativos.

O parser da CentralNovel extrai apenas o nome do autor, sem o rótulo `Autor:`.
O NovelsBr usa o `h2.chapter-title` para o título do capítulo. Os testes não
removem rótulos ou sufixos do resultado para fazê-lo coincidir com a expectativa:
essas escolhas pertencem aos scrapers, e a comparação dos campos é exata.

## Como executar

No PowerShell, na raiz do projeto:

```powershell
.\venv\Scripts\python.exe -X utf8 -m pytest src/tests/test_sse.py -q -rs
```

Para uma fonte específica:

```powershell
.\venv\Scripts\python.exe -X utf8 -m pytest src/tests/test_sse.py -q -rs -k centralnovel
```

O antigo cenário de sucesso com scraper simulado foi substituído por três
fluxos reais parametrizados. Cada fonte tem duas verificações:

1. **`test_full_sse_flow`:** roda sempre. Executa a API, seleção da fonte,
   metadados, links, download de capítulo/capa, construção do EPUB, evento SSE,
   download e limpeza do temporário. Abre o ZIP e o EPUB com `ebooklib` e
   confere capítulos não vazios, ausência dos marcadores de erro, índice,
   sequência de leitura e incorporação da capa.
2. **`test_epub_matches_manual_expectations`:** compara o EPUB gerado com o
   bloco dessa fonte no `expected.json`. Enquanto houver placeholders,
   aparece como **`skipped`**, informando os campos pendentes. Após preencher,
   roda automaticamente e precisa passar nas comparações.

Um `skip` não significa que o conteúdo foi aprovado. Os três fluxos de estrutura
continuam rodando mesmo quando as três comparações manuais estão pendentes.

Somente as respostas HTTP externas são substituídas pelas fixtures e por uma
pequena imagem sintética. As URLs precisam corresponder ao mapeamento explícito;
requisições inesperadas falham e não acessam a rede. Não são simulados o
registry, os serviços, os scrapers nem o construtor do EPUB. A autenticação
recebe um override de teste; este conjunto não testa JWT. Configuração, estado
das tarefas/SSE e diretórios de saída são isolados por fonte e restaurados
ao fim, sem modificar o `.env` ou o arquivo de benchmarks do projeto.

## Arquivos gerados para conferir

Para manter os resultados em uma pasta conhecida dentro do projeto:

```powershell
.\venv\Scripts\python.exe -X utf8 -m pytest src/tests/test_sse.py -q -rs --basetemp=diagnostics/offline-review
```

Dentro dela, cada subpasta `offline-panda*`, `offline-centralnovel*` e
`offline-novelsbr*` contém:

- `download.epub`: arquivo realmente recebido da rota de download.
- `actual.json`: metadados e texto observados dentro desse EPUB.
- `benchmarks.jsonl`: métricas locais daquela execução de teste.

`actual.json` ajuda a diagnosticar diferenças, mas **não é a referência do que
está correto**. Confira o HTML original antes de preencher ou alterar uma
expectativa. Os testes nunca sobrescrevem o `expected.json`.

## Falha total, parcial e recuperação dos capítulos

O conjunto `src/tests/test_chapter_failures.py` usa os mesmos scrapers e fluxo
de API. Simula apenas as respostas HTTP e elimina as esperas de retentativa
nos testes, preservando a lógica de tentativas do código de produção.

- **Falha total:** os metadados/índice são válidos, mas todos os capítulos
  selecionados falham após as tentativas. A tarefa termina em `failed`, o SSE
  inclui o erro sem `download_url`, o download retorna 404 e nenhum EPUB é criado.
  O POST inicial continua retornando 202, pois aceitou uma tarefa em segundo plano.
- **Falha parcial:** se pelo menos um capítulo for extraído, a tarefa termina
  em `completed` e o EPUB pode ser baixado. As posições dos capítulos que
  falharam recebem páginas `Error Chapter N` com `Content could not be downloaded.`.
  Os capítulos disponíveis e as páginas de aviso mantêm a ordem solicitada.
  O número no aviso corresponde ao capítulo original, inclusive com `start > 1`.
- **Recuperação:** um erro temporário 429 ou timeout seguido de uma resposta
  válida produz um capítulo normal, sem página de aviso para ele.

Falhas totais são exercitadas com HTTP 404, timeout e HTTP 200 contendo apenas
markup vazio. Conteúdo sem texto legível não conta como capítulo extraído.
Os testes de tarefas também verificam que progresso atrasado não reabre uma
tarefa já marcada `failed` ou `completed`.

As páginas dos capítulos 2 e 3 desses cenários são **variações sintéticas** da
fixture real do capítulo 1, com títulos e marcadores distintos para conferir
ordem e preservação. Não são capturas reais dos capítulos 2 e 3. Essa simulação
fica em `src/tests/offline_flow.py`, compartilhada com os testes de sucesso.
O `expected.json` continua sendo usado somente pelo fluxo de sucesso com a
fixture real do capítulo 1 e não é alterado por esses cenários.

```powershell
.\venv\Scripts\python.exe -X utf8 -m pytest src/tests/test_chapter_failures.py src/tests/test_task_manager.py -q
```
