# Roadmap de Melhorias Técnicas 🚀

Este documento rastreia ideias de otimização e refatoração para implementação futura.

## 1. Otimização Docker (Multi-Stage Build)
**Objetivo:** Reduzir o tamanho da imagem e aumentar a segurança.  
**Detalhes:**
- Usar um estágio builder para instalar dependências de sistema (`build-essential`, `libxml2-dev`).
- Copiar apenas os wheels ou ambiente virtual para o estágio final runner (`python-slim`).
- Remover arquivos temporários e caches.  
**Impacto:** Deploys mais rápidos e menor superfície de ataque.

## 2. Registry Auto-Discovery
**Objetivo:** Eliminar a manutenção manual de imports no src/routes/book_routes.py.  
**Detalhes:**
- Implementar um mecanismo que varre o diretório `src/classes/` ou `src/services/`.
- Importar módulos dinamicamente e registrar classes decoradas com `@ScraperRegistry.register`.
- Garantir que novos scrapers funcionem apenas criando o arquivo, sem alterar rotas.  
**Impacto:** Escalabilidade "Plug & Play" para novos sites.

## 3. Pipeline CI/CD (GitHub Actions)
**Objetivo:** Automatizar a garantia de qualidade.  
**Detalhes:**
- Criar `.github/workflows/test.yml`.
- Trigger: push e pull_request na main.
- Jobs:
    - Setup Python.
    - Install dependencies.
    - Run Lint (Ruff/Black).
    - Run Tests (`pytest -v`).  
**Impacto:** Previne que código quebrado ou sem testes chegue à produção.

## 4. Novas Funcionalidades (Webnovel)

### Rota `novel-details`
- Implementar endpoint para obter detalhes específicos de uma novel (metadados avançados, sinopse, status, etc.).

### Melhoria no Motor de Scraping
- **Tecnologias Modernas com IA**: Investigar uso de LLMs ou ferramentas de visão computacional para extração de conteúdo em sites complexos.
- **Densidade de Conteúdo**: Implementar algoritmos para detectar a área de texto principal e ignorar "ruído" (anúncios, menus) baseando-se na densidade de texto/HTML.
