# Lista de Prompts GitHub Copilot — DoneFlow

Organizada por fase, seguindo o ciclo TDD estrito (Red → Green → Refactor).

---

## FASE 0 — Setup e Configuração

**0.1 — Estrutura do projeto**
```
@workspace Crie a estrutura completa de pastas do projeto DoneFlow conforme
o PRD em docs/PRD.md. Inclua: src/doneflow/{models,services,api,repositories},
tests/{unit,integration,e2e}, .github/, docs/. Gere também o pyproject.toml
com todas as dependências: fastapi, uvicorn, sqlalchemy, pydantic>=2,
anthropic, pytest, pytest-cov, httpx, python-dotenv. Configure o pytest
com cobertura mínima de 90% e relatório em HTML.
```

**0.2 — Configuração do ambiente**
```
@workspace Crie o arquivo .env.example com todas as variáveis de ambiente
necessárias para o DoneFlow: ANTHROPIC_API_KEY, DATABASE_URL, APP_ENV,
LOG_LEVEL, AI_TIMEOUT_SECONDS, AI_CACHE_TTL_SECONDS. Crie também o
arquivo src/doneflow/config.py usando pydantic-settings para carregar
e validar essas variáveis com type hints e valores padrão seguros.
```

**0.3 — Docker**
```
@workspace Crie o Dockerfile multi-stage para o DoneFlow usando Python 3.12-slim.
Stage 1 (builder): instala dependências. Stage 2 (runtime): copia apenas
o necessário, roda com usuário não-root, expõe porta 8000, usa uvicorn
com workers configuráveis por variável de ambiente. Crie também o
docker-compose.yml com os serviços: app e um volume para o SQLite.
```

**0.4 — GitHub Actions CI**
```
@workspace Crie o workflow GitHub Actions em .github/workflows/ci.yml para
o DoneFlow. O pipeline deve: fazer checkout, configurar Python 3.12,
instalar dependências via pip, rodar o linter (ruff), checar tipos (mypy),
executar pytest com cobertura e falhar se cobertura < 90%, publicar
relatório de cobertura como artefato. Rode em push e pull_request
para as branches main e develop.
```

**0.5 — Copilot Instructions**
```
@workspace Crie o arquivo .github/copilot-instructions.md com todas as
instruções de contexto do projeto DoneFlow: stack obrigatória (Python 3.12,
FastAPI, Pydantic v2, SQLAlchemy, Anthropic API), metodologia TDD estrita
(Red→Green→Refactor), os 4 quadrantes do Eisenhower com seus enums,
padrões de nomenclatura de testes, cobertura mínima por camada e
referência ao PRD em docs/PRD.md.
```

---

## FASE 1 — Backend Core (TDD)

### Models e Enums

**1.1 — Testes do enum Quadrant (Red)**
```
@workspace Começando pelo Red do TDD, crie tests/unit/test_quadrant.py
com testes para o enum Quadrant do DoneFlow. Cubra: os 4 valores válidos
(DO_NOW, SCHEDULE, DELEGATE, ELIMINATE), rejeição de valor inválido,
conversão de string para enum, representação em português de cada quadrante
e a cor hexadecimal associada a cada um conforme seção RF-04 do PRD.
Todos os testes devem falhar neste momento.
```

**1.2 — Implementação do enum Quadrant (Green)**
```
@workspace Os testes em tests/unit/test_quadrant.py estão falhando (Red).
Crie src/doneflow/models/quadrant.py com o enum Quadrant que faça todos
os testes passarem. Inclua: os 4 valores, propriedades label (PT-BR),
color (hex) e description, método from_string() e __str__. Use type hints
e docstring completa.
```

**1.3 — Testes do modelo Task (Red)**
```
@workspace Crie tests/unit/test_task.py com testes unitários para o modelo
Task do DoneFlow. Cubra: criação com campos obrigatórios (id, text, quadrant,
created_at), validação de texto vazio ou menor que 5 caracteres, validação
de texto maior que 500 caracteres, geração automática de UUID para id,
geração automática de created_at, campo optional ai_confidence (0.0 a 1.0),
campo optional ai_reasoning. Todos devem falhar agora (Red).
```

**1.4 — Implementação do modelo Task (Green)**
```
@workspace Os testes em tests/unit/test_task.py estão no Red. Crie
src/doneflow/models/task.py com o dataclass ou Pydantic BaseModel Task
que faça todos os testes passarem. Use Pydantic v2 com Field validators,
UUID automático, datetime automático, type hints completos e docstrings.
Após passar (Green), refatore eliminando qualquer duplicação.
```

### Schemas Pydantic

**1.5 — Testes dos schemas (Red)**
```
@workspace Crie tests/unit/test_schemas.py para os schemas Pydantic v2 do
DoneFlow. Crie testes para: TaskCreate (valida texto, rejeita vazio e <5 chars,
rejeita >500 chars), TaskResponse (inclui id, text, quadrant, created_at,
ai_confidence, ai_reasoning), TaskUpdate (permite alterar quadrant manualmente),
DistributionResponse (contagem e percentual por quadrante). Todos no Red.
```

**1.6 — Implementação dos schemas (Green)**
```
@workspace Crie src/doneflow/schemas/task.py com os schemas Pydantic v2:
TaskCreate, TaskResponse, TaskUpdate e DistributionResponse. Faça todos os
testes de tests/unit/test_schemas.py passarem. Use model_validator,
field_validator, ConfigDict com from_attributes=True para compatibilidade
com SQLAlchemy. Inclua exemplos no model_config para o OpenAPI.
```

### Repositório e Banco de Dados

**1.7 — Configuração do banco (SQLAlchemy)**
```
@workspace Crie src/doneflow/database.py com a configuração do SQLAlchemy
para o DoneFlow. Inclua: engine configurado via DATABASE_URL do .env,
SessionLocal com context manager, Base declarativa, função get_db()
para injeção de dependência no FastAPI, e a tabela tasks mapeada com
todas as colunas do modelo Task (id UUID, text, quadrant, created_at,
ai_confidence, ai_reasoning). Use type hints e suporte a SQLite e PostgreSQL.
```

**1.8 — Testes do repositório (Red)**
```
@workspace Crie tests/unit/test_task_repository.py com testes para
TaskRepository usando banco SQLite em memória (:memory:). Cubra:
create() persiste e retorna Task com id gerado, get_by_id() retorna
tarefa existente, get_by_id() retorna None para id inexistente,
get_all() retorna lista completa, get_by_quadrant() filtra corretamente,
update_quadrant() altera e persiste, delete() remove e retorna True,
delete() retorna False para id inexistente, get_distribution() retorna
contagem correta por quadrante. Todos no Red.
```

**1.9 — Implementação do repositório (Green)**
```
@workspace Implemente src/doneflow/repositories/task_repository.py com
a classe TaskRepository que faça todos os testes de
tests/unit/test_task_repository.py passarem. Use SQLAlchemy Session
via injeção de dependência, type hints em todos os métodos, docstrings,
tratamento de exceções com rollback em caso de erro. Após Green, refatore
extraindo queries repetidas para métodos privados.
```

---

## FASE 2 — Serviço de IA

**2.1 — Testes do prompt builder (Red)**
```
@workspace Crie tests/unit/test_prompt_builder.py para a classe
PromptBuilder do DoneFlow. Teste que: o prompt gerado contém o texto
da tarefa, contém instrução de retorno em JSON, contém os 4 quadrantes
com descrição, contém os critérios de urgência e importância conforme
RF-03 do PRD, o output é uma string não vazia, e que palavras-chave
de urgência (hoje, urgente, deadline, prazo, cliente, entrega) estão
referenciadas nas instruções. Todos no Red.
```

**2.2 — Implementação do prompt builder (Green)**
```
@workspace Implemente src/doneflow/services/prompt_builder.py com a
classe PromptBuilder que faça todos os testes passarem. O método
build(task_text: str) -> str deve gerar um prompt estruturado que
instrua o modelo a retornar JSON com: quadrant (DO_NOW|SCHEDULE|
DELEGATE|ELIMINATE), confidence (0.0-1.0) e reasoning (string PT-BR).
Inclua os critérios da seção RF-03 do PRD. Use type hints e docstrings.
```

**2.3 — Testes do AICategorizationService com mock (Red)**
```
@workspace Crie tests/unit/test_ai_categorization_service.py para o
AICategorizationService. Use unittest.mock.AsyncMock para mockar a
Anthropic API. Cubra todos os casos da seção 6.3 do PRD:
test_task_with_urgent_keyword_classified_as_do_now,
test_task_with_strategic_keyword_classified_as_schedule,
test_low_priority_task_classified_as_eliminate,
test_ai_service_fallback_on_timeout,
test_categorization_respects_both_dimensions.
Adicione também: resposta inválida da API retorna fallback,
JSON malformado retorna fallback, confidence é float entre 0 e 1.
Todos no Red.
```

**2.4 — Implementação do AICategorizationService (Green)**
```
@workspace Implemente src/doneflow/services/ai_categorization_service.py
com a classe AICategorizationService que faça todos os testes passarem.
Use o cliente Anthropic assíncrono (AsyncAnthropic), modelo
claude-sonnet-4-20250514, timeout configurável via AI_TIMEOUT_SECONDS,
parse do JSON de resposta, fallback para SCHEDULE em caso de erro ou
timeout, log de erro sem expor dados da tarefa (LGPD - RNF-04).
Type hints e docstrings obrigatórios.
```

**2.5 — Testes do cache de categorização (Red)**
```
@workspace Crie tests/unit/test_categorization_cache.py para o
CategorizationCache do DoneFlow. Teste: cache retorna resultado para
texto já categorizado (hit), cache retorna None para texto novo (miss),
cache usa hash SHA-256 do texto como chave (não o texto puro - LGPD),
TTL expira entradas após AI_CACHE_TTL_SECONDS, cache não ultrapassa
1000 entradas (LRU eviction), estatísticas de hit/miss disponíveis.
Todos no Red.
```

**2.6 — Implementação do cache (Green)**
```
@workspace Implemente src/doneflow/services/categorization_cache.py
com CategorizationCache usando cachetools.LRUCache ou implementação
própria. Faça todos os testes de test_categorization_cache.py passarem.
Use hash SHA-256 do texto como chave (nunca o texto em si, por LGPD),
TTL via cachetools.TTLCache ou decorator, thread-safe com asyncio.Lock.
```

**2.7 — Testes do TaskService (Red)**
```
@workspace Crie tests/unit/test_task_service.py para o TaskService,
que orquestra repositório + cache + IA. Mocke TaskRepository e
AICategorizationService. Teste: create_task() chama IA e persiste,
create_task() usa cache quando disponível (não chama IA), get_all_tasks()
delega ao repositório, get_task_by_id() levanta TaskNotFoundError para
id inexistente, update_quadrant() persiste nova categoria, delete_task()
levanta TaskNotFoundError para id inexistente, get_distribution() retorna
DistributionResponse correto. Todos no Red.
```

**2.8 — Implementação do TaskService (Green)**
```
@workspace Implemente src/doneflow/services/task_service.py com TaskService
que faça todos os testes passarem. Orquestre: verificação de cache,
chamada ao AICategorizationService se cache miss, persistência via
TaskRepository, lançamento de TaskNotFoundError (exceção customizada)
para recursos inexistentes. Use injeção de dependência nos construtores,
async/await em todos os métodos, type hints e docstrings.
```

---

## FASE 3 — API REST

**3.1 — Testes dos endpoints POST e GET (Red)**
```
@workspace Crie tests/integration/test_tasks_api.py usando TestClient
do FastAPI e banco SQLite em memória. Implemente os testes da seção 6.3
do PRD: test_post_task_returns_201_with_quadrant,
test_post_empty_task_returns_422, test_get_tasks_returns_correct_distribution.
Adicione também: POST com texto <5 chars retorna 422, POST com texto >500
chars retorna 422, GET /tasks retorna lista vazia inicialmente,
GET /tasks retorna tarefa criada, response body tem todos os campos
do TaskResponse schema. Mocke AICategorizationService. Todos no Red.
```

**3.2 — Implementação do router de tasks (Green)**
```
@workspace Crie src/doneflow/api/routes/tasks.py com o APIRouter do FastAPI
implementando os 7 endpoints da seção 5.3 do PRD. Faça todos os testes de
tests/integration/test_tasks_api.py passarem. Use: Depends() para injeção
do TaskService e get_db, status codes corretos (201, 204, 404, 422),
response_model com os schemas Pydantic v2, tratamento de TaskNotFoundError
convertido para HTTPException 404, docstrings para o OpenAPI. Type hints
em todos os parâmetros e retornos.
```

**3.3 — Testes dos endpoints PATCH e DELETE (Red)**
```
@workspace Adicione em tests/integration/test_tasks_api.py os testes:
test_delete_task_removes_from_board, test_patch_task_changes_quadrant,
PATCH com quadrant inválido retorna 422, DELETE de id inexistente retorna 404,
PATCH de id inexistente retorna 404, GET /tasks/{id} retorna 200 com task,
GET /tasks/{id} com id inexistente retorna 404,
GET /tasks/distribution retorna contagem por quadrante.
Todos no Red antes de qualquer implementação.
```

**3.4 — Testes do health check (Red)**
```
@workspace Crie tests/integration/test_health.py com testes para o endpoint
GET /health do DoneFlow. Teste: retorna 200, body tem status "ok",
body tem versão da aplicação, body tem timestamp UTC atual,
body tem status do banco de dados (connected/disconnected),
response time < 100ms. Todos no Red.
```

**3.5 — Implementação do health check e app principal (Green)**
```
@workspace Crie src/doneflow/api/routes/health.py com o endpoint GET /health
e src/doneflow/main.py com a aplicação FastAPI principal. Configure:
inclusão de todos os routers com prefixo /api/v1, middleware de CORS,
middleware de logging de requisições (sem logar o corpo da tarefa - LGPD),
handler global de exceções, metadata do OpenAPI (título, versão, descrição
do DoneFlow), lifespan para criar tabelas na inicialização. Faça todos
os testes passarem.
```

**3.6 — Testes de carga e concorrência (RNF-06)**
```
@workspace Crie tests/integration/test_performance.py para validar RNF-06
(100 requisições/min) e RNF-01 (latência < 2s P95). Use pytest-asyncio
e httpx.AsyncClient. Teste: 10 requisições simultâneas de POST /tasks
completam em < 5s total, latência média de GET /tasks < 200ms,
GET /health responde em < 100ms mesmo sob carga, endpoint de distribuição
responde em < 500ms com 100 tarefas no banco.
```

---

## FASE 4 — Frontend MVP

**4.1 — Template HTML base**
```
@workspace Crie src/doneflow/static/index.html com o template base do
DoneFlow conforme o design da seção 7 do PRD. Dark-mode obrigatório
(fundo #0F1419, superfícies #1A2332). Estruture: header com nome e
breadcrumb, aside esquerdo com campo de nova tarefa e painel de
distribuição, main com board 2x2 da Matriz de Eisenhower, cada quadrante
com título, ícone, contador e área de cards. Use CSS Grid para o layout.
Fonte monoespaçada (JetBrains Mono ou similar) nos cards.
```

**4.2 — CSS do board e quadrantes**
```
@workspace Crie src/doneflow/static/css/board.css com os estilos do
board Eisenhower do DoneFlow. Implemente: grid 2x2 responsivo,
cores por quadrante (Fazer Agora #C0392B, Agendar #2980B9,
Delegar #E6A817, Eliminar #555555), cards com hover effect e botão
de remoção, animação de entrada dos cards (fade-in + slide),
loading skeleton durante categorização, painel de distribuição com
barras de progresso animadas, separador de eixos urgência/importância.
```

**4.3 — JavaScript — integração com API**
```
@workspace Crie src/doneflow/static/js/api.js com o módulo de integração
com a API REST do DoneFlow. Implemente funções async para todos os 7
endpoints da seção 5.3 do PRD: createTask(text), getAllTasks(),
getTaskById(id), updateTaskQuadrant(id, quadrant), deleteTask(id),
getDistribution(). Cada função deve: usar fetch com async/await,
tratar erros HTTP com mensagens amigáveis em PT-BR, ter JSDoc completo,
retornar dados tipados via JSDoc @typedef.
```

**4.4 — JavaScript — gerenciamento do board**
```
@workspace Crie src/doneflow/static/js/board.js com a lógica do board
Eisenhower do DoneFlow. Implemente: renderBoard(tasks) que distribui
cards nos quadrantes corretos, addCard(task) com animação de entrada,
removeCard(taskId) com animação de saída, updateDistributionPanel(distribution)
com animação das barras, showLoadingState() e hideLoadingState() no
quadrante correto, updateCounters() para os badges de cada quadrante.
Use ES6 modules, sem frameworks.
```

**4.5 — JavaScript — formulário e fluxo principal**
```
@workspace Crie src/doneflow/static/js/app.js como entry point do DoneFlow.
Implemente o fluxo completo da seção 7.2 do PRD: listener no campo de
nova tarefa (Enter e botão), validação client-side (mínimo 5 chars),
chamada a createTask() com loading indicator, renderização do card
no quadrante retornado pela IA, atualização do painel de distribuição,
handler de erro com toast notification em PT-BR, carregamento inicial
de todas as tarefas ao abrir a página. Use ES6 modules e async/await.
```

**4.6 — Servir arquivos estáticos no FastAPI**
```
@workspace Configure o FastAPI em src/doneflow/main.py para servir os
arquivos estáticos do DoneFlow. Monte StaticFiles em /static apontando
para src/doneflow/static/. Adicione rota GET / que retorna index.html.
Crie testes em tests/integration/test_frontend.py que verificam:
GET / retorna 200 e HTML, GET /static/css/board.css retorna 200,
GET /static/js/app.js retorna 200, o HTML contém o board com os
4 quadrantes.
```

---

## FASE 5 — QA e Refinamento

**5.1 — Testes E2E do fluxo completo**
```
@workspace Crie tests/e2e/test_full_flow.py com testes end-to-end do
DoneFlow usando pytest-asyncio e httpx.AsyncClient. Simule o fluxo
completo da seção 7.2 do PRD: criar tarefa urgente e verificar que
vai para DO_NOW, criar tarefa estratégica e verificar SCHEDULE,
criar tarefa delegável e verificar DELEGATE, criar tarefa dispensável
e verificar ELIMINATE, verificar distribuição após as 4 criações,
deletar uma tarefa e verificar que sai do board, reclassificar
manualmente e verificar novo quadrante.
```

**5.2 — Testes de contrato da API IA**
```
@workspace Crie tests/integration/test_ai_contract.py para validar o
contrato entre o DoneFlow e a Anthropic API. Usando mocks precisos,
verifique: o prompt enviado contém os campos obrigatórios (texto da tarefa,
instrução de JSON, 4 quadrantes), o modelo usado é claude-sonnet-4-20250514,
max_tokens está configurado, timeout é respeitado, resposta com quadrant
inválido é tratada com fallback, resposta sem campo confidence usa 0.5
como padrão.
```

**5.3 — Testes de segurança e LGPD (RNF-04)**
```
@workspace Crie tests/unit/test_lgpd_compliance.py para validar os
requisitos de privacidade RNF-04 do DoneFlow. Verifique que: o cache
usa hash SHA-256 e não armazena o texto original, os logs de erro não
incluem o texto da tarefa, o health endpoint não expõe dados internos
sensíveis, o middleware de logging não loga o body do POST /tasks,
headers de resposta incluem X-Content-Type-Options e X-Frame-Options.
```

**5.4 — Relatório de cobertura e gaps**
```
@workspace Rode pytest --cov=src/doneflow --cov-report=term-missing
e analise os gaps de cobertura. Para cada módulo abaixo de 90%,
crie testes adicionais que cubram os branches não testados. Priorize:
tratamento de exceções, casos de borda nos validators Pydantic,
branches do cache (hit/miss/expired), e o fallback do AICategorizationService.
O objetivo é atingir >= 90% geral e >= 95% em unit tests conforme RNF-03.
```

**5.5 — Refinamento do prompt de IA**
```
@workspace Analise os resultados dos testes de categorização em
tests/unit/test_ai_categorization_service.py. Refine o prompt em
src/doneflow/services/prompt_builder.py para melhorar a precisão.
Adicione: exemplos few-shot com os 4 quadrantes (2 exemplos cada),
instrução explícita de responder SOMENTE em JSON sem markdown,
lista expandida de palavras-chave PT-BR por quadrante conforme RF-03,
instrução de usar confidence < 0.6 quando ambíguo. Atualize os testes.
```

**5.6 — Documentação OpenAPI e README**
```
@workspace Complete a documentação do DoneFlow. No main.py, enriqueça
o OpenAPI com: descrição completa de cada endpoint, exemplos de request
e response para todos os schemas, tags organizadas por módulo (Tasks,
Health), erros documentados (422, 404, 500). Crie README.md com:
badges de CI e cobertura, descrição do projeto, como rodar localmente
(Docker e sem Docker), como rodar os testes, estrutura de pastas e
link para o PRD.
```

---

## Resumo por Fase

| Fase | Prompts | Entregáveis Principais |
|---|---|---|
| 0 — Setup | 5 | Estrutura, Docker, CI, Copilot Instructions |
| 1 — Backend Core | 9 | Models, Schemas, Repositório, Banco |
| 2 — Serviço de IA | 8 | Prompt Builder, Cache, AI Service, TaskService |
| 3 — API REST | 6 | 7 endpoints, health check, testes de carga |
| 4 — Frontend | 6 | HTML, CSS, JS, integração com API |
| 5 — QA | 6 | E2E, LGPD, cobertura >= 90%, docs |
| **Total** | **40** | **MVP completo com TDD** |

---

> **Dica de uso:** Execute cada prompt em sequência dentro do Copilot Chat com `@workspace`. Sempre rode `pytest` após cada Green antes de passar para o próximo prompt — o ciclo Red→Green→Refactor é inviolável.