# DONEFLOW
## Matriz de Eisenhower · IA

**Product Requirements Document (PRD)**

**Categorização Automática de Tarefas por IA**
*Aplicação Web Full-Stack com FastAPI + TDD*

| Campo | Valor |
|---|---|
| **Versão** | 1.0 |
| **Data** | 23 de Maio de 2026 |
| **Status** | Draft — Em Revisão |
| **Responsável** | Product Owner / Tech Lead |
| **Metodologia** | TDD · Python · FastAPI · PyCharm + GitHub Copilot |
| **Confidencialidade** | Interno |

---

# 1. Visão Geral do Produto

## 1.1 Declaração do Produto

O DoneFlow é uma aplicação web de gerenciamento de tarefas que utiliza Inteligência Artificial para categorizar automaticamente as tarefas do usuário segundo a Matriz de Eisenhower, classificando-as em quatro quadrantes: Fazer Agora, Agendar, Delegar e Eliminar. O sistema analisa contexto, urgência e impacto estratégico de cada tarefa, eliminando o esforço cognitivo de priorização manual.

## 1.2 Problema

Profissionais e equipes perdem tempo significativo decidindo a prioridade de cada tarefa no início do dia ou da semana. A Matriz de Eisenhower é uma ferramenta consagrada de produtividade, porém a aplicação manual exige julgamento constante e é propensa a vieses cognitivos. Atualmente não existe uma ferramenta simples, integrada e orientada por IA que automatize esse processo de forma confiável.

## 1.3 Proposta de Valor

- Classificação automática e inteligente de tarefas em menos de 2 segundos
- Interface visual intuitiva baseada em design dark-mode profissional
- Distribuição em tempo real entre os quatro quadrantes da Matriz de Eisenhower
- Histórico e rastreabilidade de tarefas por quadrante
- API RESTful extensível para integrações futuras

## 1.4 Público-Alvo

| Persona | Perfil | Necessidade Principal |
|---|---|---|
| Profissional Corporativo | Analista, gerente ou coordenador com muitas demandas diárias | Priorizar rapidamente sem análise manual |
| Empreendedor / Fundador | Responsável por múltiplas frentes simultâneas | Focar no que gera mais impacto estratégico |
| Estudante / Freelancer | Agenda variável com projetos paralelos | Organizar tarefas com clareza e agilidade |
| Líder de Equipe | Distribui e acompanha entregas do time | Delegar com critério baseado em urgência e impacto |

---

# 2. Requisitos de Negócio

## 2.1 Objetivos Estratégicos

1. Lançar MVP funcional com categorização por IA em até 8 semanas
2. Alcançar taxa de acerto da IA superior a 85% validada por usuários
3. Garantir experiência de uso fluida com latência de categorização inferior a 2s
4. Estabelecer base de código sustentável com cobertura de testes >= 90% (TDD)

## 2.2 Critérios de Sucesso

| KPI | Meta MVP | Período de Medição |
|---|---|---|
| Taxa de acerto da categorização IA | >= 85% de aprovação pelo usuário | Primeiros 30 dias pós-lançamento |
| Latência de resposta da API | < 2 segundos por tarefa | Monitoramento contínuo |
| Cobertura de testes (TDD) | >= 90% | A cada sprint |
| Uptime da aplicação | >= 99.5% | Mensal |
| Usuários ativos no MVP | 50 usuários validadores | Primeiros 60 dias |

---

# 3. Requisitos Funcionais

## 3.1 Módulo de Entrada de Tarefas

### RF-01 — Criação de Tarefa

O usuário deve poder inserir uma nova tarefa através de um campo de texto simples ("Descreva sua tarefa..."). A tarefa deve ser enviada ao sistema para categorização automática via IA.

- Campo de texto livre com placeholder descritivo
- Validação mínima: tarefa não pode estar vazia e deve ter ao menos 5 caracteres
- Suporte a tarefas em Português e Inglês

### RF-02 — Envio para Categorização

Ao submeter a tarefa, o sistema deve acionar o serviço de IA e retornar a categorização com o quadrante correspondente da Matriz de Eisenhower em até 2 segundos.

## 3.2 Módulo de Categorização por IA

### RF-03 — Análise Contextual

A IA deve analisar o texto da tarefa considerando os seguintes fatores para determinar urgência e importância:

- Palavras-chave indicadoras de urgência: `hoje`, `urgente`, `deadline`, `agora`, `prazo`, `cliente`, `entrega`
- Palavras-chave de importância estratégica: `roadmap`, `produto`, `estratégia`, `proposta`, `reunião`, `CEO`
- Verbos de ação e contexto profissional vs. pessoal

### RF-04 — Classificação nos Quadrantes

| Quadrante | Critério IA | Ação Recomendada | Cor |
|---|---|---|---|
| **Fazer Agora** | Alta urgência + Alta importância | Execute imediatamente | Vermelho `#C0392B` |
| **Agendar** | Baixa urgência + Alta importância | Planeje e programe | Azul `#2980B9` |
| **Delegar** | Alta urgência + Baixa importância | Transfira para outro | Amarelo `#E6A817` |
| **Eliminar** | Baixa urgência + Baixa importância | Descarte ou adie | Cinza `#555555` |

## 3.3 Módulo do Board — Matriz de Eisenhower

### RF-05 — Exibição do Board

O board deve exibir os quatro quadrantes da matriz em layout 2×2, com cards de tarefas posicionados automaticamente de acordo com a categorização da IA. Cada quadrante deve exibir contador de tarefas.

### RF-06 — Cards de Tarefa

- Exibir texto completo da tarefa em fonte monoespaçada
- Indicar visualmente o quadrante com cor e ícone correspondentes
- Permitir remoção manual de tarefas pelo usuário
- Permitir reclassificação manual (drag-and-drop entre quadrantes — v1.1)

## 3.4 Módulo de Distribuição e Estatísticas

### RF-07 — Painel de Distribuição

O painel lateral deve exibir a distribuição percentual de tarefas por quadrante com barras de progresso coloridas, totalizando a contagem de tarefas em cada categoria. O painel também deve exibir texto explicativo sobre a Matriz de Eisenhower.

---

# 4. Requisitos Não Funcionais

| ID | Categoria | Requisito | Critério de Aceitação |
|---|---|---|---|
| RNF-01 | Desempenho | Categorização via IA | Resposta < 2s em P95 |
| RNF-02 | Disponibilidade | Uptime da API | >= 99.5% mensal |
| RNF-03 | Testabilidade | Cobertura de testes | >= 90% (TDD obrigatório) |
| RNF-04 | Segurança | Proteção de dados | LGPD-compliant; sem log de tarefas pessoais |
| RNF-05 | Manutenibilidade | Código limpo | PEP8 + type hints + docstrings |
| RNF-06 | Escalabilidade | Concorrência | Suporte a 100 requisições/min no MVP |
| RNF-07 | Usabilidade | Responsividade | Funcional em desktop (min. 1280px) e tablet |
| RNF-08 | Internacionalização | Idioma | PT-BR como língua principal; EN suportado pela IA |

---

# 5. Arquitetura Técnica

## 5.1 Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend / API | Python 3.12 + FastAPI | Alta performance, tipagem nativa, suporte a async |
| IA / NLP | Anthropic Claude API (`claude-sonnet-4`) | Melhor compreensão contextual em PT-BR |
| Validação de Dados | Pydantic v2 | Integrado ao FastAPI; schemas tipados |
| ORM / Banco | SQLAlchemy + SQLite (MVP) / PostgreSQL (prod) | Migrações simples, escalável |
| Testes | pytest + pytest-cov + httpx | TDD nativo; cobertura completa |
| IDE | PyCharm + GitHub Copilot | Autocompletar IA e sugestão de testes |
| Frontend (MVP) | HTML5 + CSS3 + Vanilla JS | Sem overhead de framework no MVP |
| Infraestrutura | Docker + uvicorn | Portabilidade e deploy simplificado |

## 5.2 Arquitetura de Componentes

A aplicação segue arquitetura em camadas desacopladas, facilitando a evolução e testabilidade:

- **Camada de Apresentação:** Interface web com board Kanban e painel de distribuição
- **Camada de API:** Endpoints REST via FastAPI com validação Pydantic
- **Camada de Serviço:** Lógica de negócio isolada (`TaskService`, `AICategorizationService`)
- **Camada de IA:** Client de integração com Anthropic API (prompt engineering estruturado)
- **Camada de Dados:** Repositório de tarefas com SQLAlchemy

## 5.3 Endpoints da API (v1)

| Método | Endpoint | Descrição | Status Codes |
|---|---|---|---|
| `POST` | `/api/v1/tasks` | Criar tarefa e categorizar via IA | 201, 422, 500 |
| `GET` | `/api/v1/tasks` | Listar todas as tarefas | 200 |
| `GET` | `/api/v1/tasks/{id}` | Buscar tarefa por ID | 200, 404 |
| `PATCH` | `/api/v1/tasks/{id}` | Reclassificar tarefa manualmente | 200, 404, 422 |
| `DELETE` | `/api/v1/tasks/{id}` | Remover tarefa | 204, 404 |
| `GET` | `/api/v1/tasks/distribution` | Estatísticas por quadrante | 200 |
| `GET` | `/health` | Health check da API | 200 |

---

# 6. Estratégia de Testes (TDD)

## 6.1 Filosofia TDD

Toda funcionalidade será desenvolvida seguindo estritamente o ciclo **Red → Green → Refactor**. Nenhum código de produção será escrito sem um teste que o justifique. O GitHub Copilot será utilizado como assistente de sugestão, mas a lógica de teste é definida pelo desenvolvedor.

## 6.2 Pirâmide de Testes

| Camada | Tipo | Ferramentas | Meta de Cobertura |
|---|---|---|---|
| Unitários | Funções, services, modelos isolados | pytest + unittest.mock | >= 95% |
| Integração | Endpoints FastAPI + DB + AI mock | pytest + httpx + TestClient | >= 90% |
| E2E / Contrato | Fluxo completo de categorização | pytest + requests | >= 80% |

## 6.3 Casos de Teste Prioritários

### Serviço de Categorização IA

- `test_task_with_urgent_keyword_classified_as_do_now`
- `test_task_with_strategic_keyword_classified_as_schedule`
- `test_low_priority_task_classified_as_eliminate`
- `test_ai_service_fallback_on_timeout`
- `test_categorization_respects_both_dimensions`

### API Endpoints

- `test_post_task_returns_201_with_quadrant`
- `test_post_empty_task_returns_422`
- `test_get_tasks_returns_correct_distribution`
- `test_delete_task_removes_from_board`
- `test_patch_task_changes_quadrant`

### Modelos e Schemas

- `test_task_schema_validates_required_fields`
- `test_quadrant_enum_accepts_only_valid_values`
- `test_task_repository_persists_and_retrieves`

---

# 7. Design e Experiência do Usuário

## 7.1 Princípios de Design

- Dark-mode profissional como padrão (fundo `#0F1419`, superfícies `#1A2332`)
- Tipografia monoespaçada nos cards para identidade visual técnica
- Cores semânticas por quadrante: vermelho (urgente), azul (importante), amarelo (delegar), cinza (eliminar)
- Feedback visual imediato: loading state durante categorização, animação suave de inserção do card
- Layout 2×2 simétrico da matriz com separador vertical de urgência

## 7.2 Fluxo Principal do Usuário

1. Usuário acessa o DoneFlow (board vazio ou com tarefas existentes)
2. Digita a descrição da tarefa no campo "Descreva sua tarefa..."
3. Pressiona Enter ou clica em "Adicionar" — sistema exibe loading indicator
4. IA processa e retorna o quadrante em < 2 segundos
5. Card aparece no quadrante correto com animação de entrada
6. Painel de distribuição atualiza os contadores e barras em tempo real
7. Usuário pode visualizar, mover ou remover o card conforme necessário

## 7.3 Componentes da Interface

| Componente | Descrição | Versão |
|---|---|---|
| Header / Nav | Nome da aplicação, breadcrumb e ações globais | MVP |
| Campo Nova Tarefa | Input de texto com placeholder e botão de envio | MVP |
| Board 2×2 | Quatro quadrantes com título, ícone, contador e cards | MVP |
| Cards de Tarefa | Texto em mono, cor do quadrante, botão de remoção | MVP |
| Painel de Distribuição | Barras por quadrante com contagem e percentual | MVP |
| Sobre a Matriz | Texto explicativo sobre a Matriz de Eisenhower | MVP |
| Drag-and-Drop | Mover cards entre quadrantes manualmente | v1.1 |
| Filtros e Busca | Filtrar tarefas por quadrante ou texto | v1.1 |
| Exportar | Exportar lista por quadrante em CSV/PDF | v2.0 |

---

# 8. Roadmap e Fases de Entrega

| Fase | Descrição | Entregáveis | Prazo Estimado |
|---|---|---|---|
| **Fase 0** — Setup | Configuração do projeto, ambiente e CI | Estrutura de pastas, pytest config, Dockerfile, GitHub Actions | Semana 1 |
| **Fase 1** — Backend Core | Modelos, schemas, repositório e testes unitários (TDD) | Task model, Pydantic schemas, SQLAlchemy repo, 100% test unitário | Semanas 1–2 |
| **Fase 2** — IA Service | Integração com Anthropic API + mock para testes | `AICategorizationService`, prompt template, testes com mock | Semanas 2–3 |
| **Fase 3** — API REST | Endpoints FastAPI completos com testes de integração | 5 endpoints funcionais, TestClient tests, OpenAPI docs | Semanas 3–4 |
| **Fase 4** — Frontend MVP | Interface web com board e painel de distribuição | Board 2×2, cards dinâmicos, painel lateral, dark-mode | Semanas 5–6 |
| **Fase 5** — QA & Refinamento | Testes E2E, ajuste de prompts, validação com usuários | Cobertura >= 90%, relatório de acerto da IA, bugs resolvidos | Semanas 7–8 |
| **v1.1** — Melhorias | Drag-and-drop, filtros, autenticação básica | Funcionalidades extras, login JWT | Semanas 9–12 |

---

# 9. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|---|---|---|---|
| Latência elevada da Anthropic API | Alto | Média | Cache de respostas por hash do texto; timeout configurável; fallback com classificador local simples |
| Taxa de acerto da IA abaixo de 85% | Alto | Baixa | Iteração de prompt engineering; coleta de feedback do usuário; validação com dataset de tarefas reais |
| Mudança de preço/disponibilidade da API IA | Médio | Baixa | Abstração da camada de IA para trocar de provedor sem alterar o core |
| Complexidade de testes com mocks de IA | Médio | Média | Definir contratos claros; fixtures reutilizáveis; separar teste de integração dos unitários |
| Escopo crescente (scope creep) | Médio | Alta | Backlog priorizado; MVP estritamente definido; features v1.1+ em lista separada |

---

# 10. Glossário

| Termo | Definição |
|---|---|
| **Matriz de Eisenhower** | Framework de priorização que classifica tarefas em dois eixos: urgência e importância, resultando em quatro quadrantes de ação |
| **TDD** | Test-Driven Development — metodologia onde os testes são escritos antes do código de produção |
| **FastAPI** | Framework Python moderno e de alta performance para construção de APIs RESTful com tipagem nativa e documentação automática |
| **Pydantic** | Biblioteca Python para validação de dados e definição de schemas utilizando type hints |
| **GitHub Copilot** | Assistente de codificação por IA integrado ao IDE (PyCharm) que sugere código e testes com base no contexto |
| **Claude API** | API da Anthropic para acesso a modelos de linguagem de grande escala (LLMs) utilizados para a categorização contextual de tarefas |
| **MVP** | Minimum Viable Product — versão mínima funcional do produto com as funcionalidades essenciais para validação |
| **P95** | Percentil 95 — métrica de latência que indica o tempo de resposta abaixo do qual ocorrem 95% das requisições |

---

*DoneFlow — PRD v1.0 | Documento Confidencial*
*Gerado em 23 de Maio de 2026 | Metodologia TDD · Python · FastAPI · PyCharm + GitHub Copilot*