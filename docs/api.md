# Uso da API

Inicie o servidor conforme o [README](../README.md). A referência gerada pelo
FastAPI fica em `/docs`, com o esquema em `/openapi.json`.

## Endpoints

| Método e caminho | Uso | Autenticação |
| --- | --- | --- |
| `GET /` | Estado do serviço | Pública |
| `GET /search/` | Busca por `source` e `query` | Pública |
| `POST /dev/token` | Emite JWT de teste por uma hora | Somente com `DEBUG=true` e acesso local |
| `POST /books/generate` | Inicia uma geração | JWT quando configurado |
| `GET /books/events/{task_id}` | Stream de progresso SSE | JWT quando configurado |
| `GET /books/download/{task_id}` | Download do EPUB pronto | JWT quando configurado |
| `GET /debug-proxy` | Consulta IP de saída e informação de proxy | Pública; chama serviço externo |
| `GET /debug-headers` | Inspeciona os headers da sessão HTTP | Pública; chama serviço externo |

## Autenticação

Quando `API_JWT_SECRET` está definido, todas as rotas `/books` exigem
`Authorization: Bearer <token>`. O token usa HS256, o mesmo segredo do servidor
e `action: "generate-epub"`. O fluxo foi preparado para um backend intermediário,
como uma Edge Function, assinar os tokens. Não coloque o segredo no frontend.

O código registra `sub` e `tier`, mas atualmente não exige esses dois campos.
Tokens inválidos ou ausentes recebem `401`; uma ação diferente recebe `403`.
Sem segredo configurado, a verificação é dispensada para desenvolvimento.
Os testes offline de geração substituem essa autenticação; não a validam.

### Gerar um token pelo Swagger local

Para testar a autenticação sem gerar tokens pelo terminal:

1. No `.env`, defina `DEBUG=true` e preencha `API_JWT_SECRET` com um segredo local.
2. Reinicie a API e abra `http://127.0.0.1:8000/docs`.
3. Em **Local development**, execute `POST /dev/token` com **Try it out → Execute**.
4. Copie o campo `access_token` da resposta. Em **Authorize**, cole somente o
   token, sem o prefixo `Bearer`, e confirme em **Authorize**.
5. Execute as rotas `/books` pelo Swagger; o header será enviado automaticamente.

O token vale por uma hora e usa a identidade `local-test`, `tier: premium` e
`action: generate-epub`. Quando expirar, gere outro e atualize **Authorize**.
O segredo permanece no servidor; a resposta contém somente o token e sua validade.

A rota não é registrada com `DEBUG=false` e aceita somente conexões de loopback
com host local (`localhost`, `127.0.0.1` ou `::1`). Origens de outras páginas são
recusadas. Use diretamente a API local, sem proxy reverso, e mantenha `DEBUG=false`
na publicação. A autenticação das rotas `/books` continua ativa com o segredo
preenchido, mesmo com `DEBUG=true`.

## Exemplo local no PowerShell

Com `.env.example` copiado e segredo vazio:

```powershell
$api = "http://127.0.0.1:8000"
$headers = @{}

# Se o servidor exigir JWT, use um token assinado pelo backend autorizado:
# $headers = @{ Authorization = "Bearer $token" }

Invoke-RestMethod -Uri "$api/search/?source=royal&query=mother"

$novel = [uri]::EscapeDataString("https://novelphoenix.com/novel/shadow-slave")
$task = Invoke-RestMethod -Method Post -Headers $headers -Uri "$api/books/generate?url=$novel&qty=3&start=1"
$task
```

`url`, `qty` e `start` são **query parameters**, mesmo sendo um POST. `qty`
tem padrão 1 e limite definido por `MAX_CHAPTERS_LIMIT`; `start` começa em 1.
Domínio não suportado retorna `400`; parâmetros fora dos limites retornam `422`.
O POST cria uma tarefa nova a cada chamada, sem deduplicação.

Resposta de aceitação:

```json
{
  "task_id": "identificador",
  "message": "Generation started",
  "status_url": "/books/events/identificador"
}
```

A geração começa em segundo plano após a resposta. O `202` confirma a
aceitação; erros posteriores aparecem no estado da tarefa.

## Acompanhar o progresso

Use o mesmo terminal até o stream terminar. Em outro terminal, defina `$api`
e o identificador da tarefa antes de executar o comando:

```powershell
curl.exe -N "$api$($task.status_url)"
# Com autenticação: acrescente -H "Authorization: Bearer $token"
```

O servidor verifica mudanças a cada 0,5 segundo e envia eventos nomeados
`update` com JSON. Os estados são `pending`, `processing`, `completed` e
`failed`.

```text
event: update
data: {"status":"processing","progress":55}

event: update
data: {"status":"completed","progress":100,"download_url":"/books/download/identificador"}
```

No estado `failed`, o evento inclui `error`. Um identificador inexistente
gera um evento `error` com `message: "Task not found"` e encerra o stream;
essa situação não é hoje uma resposta HTTP 404 convencional.

O percentual cobre preparação (5–15%), capítulos (15–95%), montagem do EPUB
(98%) e arquivo pronto (100%). A API não expõe contagens exatas de capítulos
baixados/falhos; capítulos processados com falha também avançam o percentual.
Atualizações podem ser agrupadas entre duas verificações do stream.

O `EventSource` nativo do navegador não permite definir o header Bearer.
Para esse contrato, use leitura de SSE via `fetch` ou um intermediário que
encaminhe autenticação e streaming. O cliente deve encerrar o acompanhamento
ao receber `completed` ou `failed` e tratar reconexões quando necessário.

## Download e limites atuais

Após receber `completed`:

```powershell
Invoke-WebRequest -Headers $headers -Uri "$api/books/download/$($task.task_id)" -OutFile "outputs/novel.epub"
```

A resposta usa `application/epub+zip`. O arquivo e a tarefa são removidos
após o envio, portanto o download não é um link permanente. Antes de ficar
pronto, ou depois de removida a tarefa, essa rota retorna `404`. Se o estado
existir mas o arquivo tiver sido perdido, retorna `500`.

O modelo atual é suficiente para uma instância pequena, com estas condições:

- Tarefas ficam em memória: um reinício perde o estado e interrompe a geração.
- Use um único processo/instância, pois o estado não é compartilhado.
- Desconectar do SSE não cancela a geração. Enquanto a tarefa existir, outro
  stream com o mesmo ID recebe seu estado atual, sem reproduzir todo o histórico.
- O POST não espera o scraping, mas o stream depende dos limites de rede,
  proxy e hospedagem. A biblioteca SSE envia pings periódicos.
- A montagem do EPUB ainda executa no event loop e pode pausar atualizações.
- Falhas parciais preservam páginas de aviso no EPUB; falha em todos os
  capítulos impede a geração.

Não há hoje rota de cancelamento, consulta de estado JSON ou fila persistente.
