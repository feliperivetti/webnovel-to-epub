# Roadmap de Melhorias Técnicas 🚀

Este documento rastreia ideias de otimização, refatoração e novas funcionalidades para implementação futura.

## 🚧 Pendente / Em Andamento

### 1. Finalização de Benchmarks
**Objetivo:** Validar performance e escalabilidade.
**Detalhes:**
- Consolidar script de benchmark (`scripts/run_benchmarks.py`).
- Executar testes de carga (Low/Medium/High) para comparar configurações (Proxies vs Direct).
- Gerar relatório final de métricas (capítulos/segundo).

## 🔮 Futuras Implementações

### 2. Rate Limiting Global
**Objetivo:** Evitar bloqueios por excesso de requisições.
**Detalhes:**
- Implementar limitação de requisições por domínio (ex: 1 req/seg para RoyalRoad).
- Usar token bucket ou leaky bucket algorithm.
**Impacto:** Maior resiliência e menor risco de banimento de IP/Proxy.

### 3. Camada de Cache (Redis)
**Objetivo:** Reduzir latência e requisições repetidas.
**Detalhes:**
- Cachear metadados de novels (título, autor, capa) por 24h.
- Cachear lista de capítulos para evitar scraping repetido em curto período.
**Impacto:** Resposta instantânea para livros populares.

### 4. Rota `novel-details`
**Objetivo:** Enriquecer a experiência do frontend.
**Detalhes:**
- Endpoint dedicado para retornar sinopse, tags, status (em andamento/concluído) e estatísticas.

### 5. Melhoria no Motor de Scraping (IA)
**Objetivo:** Lidar com sites anti-scraping ou complexos.
**Detalhes:**
- Investigar uso de LLMs para extrair conteúdo de HTML sujo.
- Algoritmos de densidade de texto para remover anúncios e menus automaticamente.
