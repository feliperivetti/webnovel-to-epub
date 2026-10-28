# Configurar um proxy Webshare

O backend aceita um principal em `PROXY_URL` e um alternativo em
`PROXY_URL_FALLBACK`. O frontend chama a API sem receber essas credenciais.
Não é necessário instalar a extensão da Webshare no navegador.

## Configuração inicial

1. Abra a lista de proxies no painel da Webshare e selecione conexão **Direct**,
   protocolo **HTTP** e autenticação por usuário e senha.
2. Escolha uma linha da lista e localize endereço, porta, usuário e senha.
3. Preencha o `.env` local com os dados reais dessa linha:

   ```dotenv
   PROXY_URL="http://USUARIO:SENHA@ENDERECO:PORTA"
   PROXY_URL_FALLBACK=
   ```

4. Opcionalmente, coloque os dados de uma segunda linha no fallback, com o mesmo
   formato. Não cole a lista inteira em uma variável.
5. Reinicie o servidor após salvar o `.env`.

O esquema `http://` descreve a conexão com o proxy e pode ser usado para acessar
os sites HTTPS. Use a porta do painel. Se usuário ou senha contiverem caracteres
reservados de URL, como `@`, `:` ou `#`, codifique os componentes das credenciais
(percent-encoding). Use as credenciais do proxy, não o token da API Webshare.
Mantenha as credenciais no `.env` local ou nos segredos da hospedagem.

## Verificação pelo Swagger

1. Em `http://127.0.0.1:8000/docs`, execute `GET /debug-proxy`.
2. Confira `proxy_configured: true`, `error: null` e um IP em `server_ip_check`.
   Na conexão Direct, compare o IP com o endereço escolhido no painel.
3. Faça uma busca e gere um EPUB de um a três capítulos. Use o JWT em **Authorize**
   para as rotas `/books`.
4. Confira o conteúdo do EPUB. A consulta de IP não comprova acesso às novels.

Se `error` for `ProxyError`, confira endereço, porta, credenciais, autenticação
e disponibilidade no painel. O diagnóstico mostra somente a classe do erro
para evitar expor credenciais. `HTTPError` indica uma resposta HTTP de erro da
consulta de IP. Não desative a verificação de certificados TLS.

Variáveis `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` e `NO_PROXY` também podem
interferir nas conexões do Requests. Evite configurações conflitantes.

## Hospedagem

Cadastre `PROXY_URL` e, se utilizado, `PROXY_URL_FALLBACK` como variáveis/segredos
do serviço hospedado e reinicie ou publique novamente. O `.env` local não entra
na imagem Docker. Use `DEBUG=false` e configure também `API_JWT_SECRET`.

A autenticação por usuário/senha permite usar conexões com IPs de origem
diferentes sem cadastrar cada saída da hospedagem na autorização por IP da
Webshare. Valide novamente IP, busca e geração na hospedagem.

## Limites atuais

- Não há rotação automática pela lista dos dez proxies.
- O principal atende buscas, metadados, listagem, capítulos e capas.
- O fallback cobre certos erros de conexão nas tentativas de capítulos; não
  cobre todas as etapas nem é acionado por HTTP 403/429.
- Falhas não provocam uma troca automática geral para acesso direto.
- A Webshare informa dez proxies de datacenter compartilhados e até 1 GB/mês
  no plano gratuito. O tráfego de todos os usuários do backend compartilha a
  franquia. HTML, capas e novas tentativas consomem tráfego. Confira no painel.

Referências: [plano gratuito](https://help.webshare.io/en/articles/8375287-do-you-offer-proxies-for-free)
e [conexão e autenticação](https://apidocs.webshare.io/proxy-connection).
