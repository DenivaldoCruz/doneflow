"""Prompt builder for structured Eisenhower matrix classification instructions."""

from __future__ import annotations


class PromptBuilder:
    """Build prompts for AI task categorization.

    The generated prompt instructs the model to classify a task into one of the
    Eisenhower quadrants and return only valid JSON.
    """

    def build(self, task_text: str) -> str:
        """Build a structured classification prompt.

        Args:
            task_text: Raw task description provided by the user.

        Returns:
            A PT-BR prompt with RF-03 criteria, few-shot examples, and strict JSON output guidance.
        """
        return f"""
Você é um classificador de tarefas usando a Matriz de Eisenhower.

Analise a tarefa abaixo considerando os critérios de urgência e importância (RF-03):
- Urgência: sinais de tempo curto, pressão imediata, deadline e consequências de atraso.
- Importância: impacto estratégico, alinhamento com objetivos, valor de longo prazo.
- Impacto e consequências: avalie impacto no negócio, no cliente e no resultado esperado.
- Verbos de ação e contexto profissional vs. pessoal.
- Se houver sinais conflitantes, poucos detalhes ou contexto ambíguo, escolha o melhor
  quadrante possível, mas use confidence < 0.6.

Palavras-chave PT-BR expandidas por quadrante conforme RF-03:
- DO_NOW (urgente e importante): hoje, urgente, deadline, agora, prazo, cliente, entrega,
  crítico, incidente, bloqueio, produção, contrato, receita, CEO, proposta, escalado.
- SCHEDULE (não urgente e importante): roadmap, produto, estratégia, proposta, reunião,
  CEO, planejar, trimestre, objetivo, melhoria, arquitetura, métricas, OKR, pesquisa,
  planejamento, revisão, carreira.
- DELEGATE (urgente e não importante): responder, administrativo, rotina, solicitação,
  operacional, acompanhar, cobrar, confirmar, agendar, encaminhar, suporte, fornecedor,
  triagem, status, formulário.
- ELIMINATE (não urgente e não importante): sem prazo, baixo impacto, opcional, talvez,
  arquivo, organizar, figurinhas, distração, curiosidade, navegar, limpar, antigo,
  irrelevante, entretenimento, depois.

Quadrantes possíveis (use exatamente estes nomes):
- DO_NOW: urgente e importante
- SCHEDULE: não urgente e importante
- DELEGATE: urgente e não importante
- ELIMINATE: não urgente e não importante

Exemplos few-shot (use como referência de decisão e formato):
1. Tarefa: "Resolver incidente crítico de produção para cliente hoje"
   Resposta: {{"quadrant": "DO_NOW", "confidence": 0.94, "reasoning": "Urgente e importante por afetar cliente e produção."}}
2. Tarefa: "Enviar proposta urgente ao CEO antes do deadline"
   Resposta: {{"quadrant": "DO_NOW", "confidence": 0.91, "reasoning": "Prazo imediato com impacto executivo e comercial."}}
3. Tarefa: "Definir roadmap de produto do próximo trimestre"
   Resposta: {{"quadrant": "SCHEDULE", "confidence": 0.88, "reasoning": "Importante para estratégia, sem urgência imediata."}}
4. Tarefa: "Planejar reunião estratégica de melhoria com a liderança"
   Resposta: {{"quadrant": "SCHEDULE", "confidence": 0.84, "reasoning": "Importante e planejável, sem pressão de hoje."}}
5. Tarefa: "Responder solicitação administrativa urgente agora"
   Resposta: {{"quadrant": "DELEGATE", "confidence": 0.79, "reasoning": "Urgente, porém operacional e delegável."}}
6. Tarefa: "Confirmar entrega operacional com fornecedor ainda hoje"
   Resposta: {{"quadrant": "DELEGATE", "confidence": 0.75, "reasoning": "Tem prazo curto, mas baixo valor estratégico direto."}}
7. Tarefa: "Organizar figurinhas antigas sem prazo"
   Resposta: {{"quadrant": "ELIMINATE", "confidence": 0.83, "reasoning": "Baixa urgência e baixo impacto."}}
8. Tarefa: "Pesquisar curiosidades opcionais de baixo impacto"
   Resposta: {{"quadrant": "ELIMINATE", "confidence": 0.81, "reasoning": "Opcional, sem urgência nem importância clara."}}

Tarefa para classificar:
"{task_text}"

Responda SOMENTE em JSON válido, sem markdown, sem texto extra, no formato:
{{
  "quadrant": "DO_NOW|SCHEDULE|DELEGATE|ELIMINATE",
  "confidence": 0.0,
  "reasoning": "explicação curta em PT-BR"
}}

Regras de saída:
- "quadrant" deve ser um dos 4 valores exatos.
- "confidence" deve ser número entre 0.0 e 1.0.
- Use confidence < 0.6 quando a tarefa for ambígua, genérica ou sem contexto suficiente.
- "reasoning" deve ser string em português (PT-BR).
- Não use blocos de código, markdown, comentários ou qualquer texto fora do JSON.
""".strip()

    def build_prompt(self, task_text: str) -> str:
        """Backward-compatible wrapper for prompt generation.

        Args:
            task_text: Raw task description provided by the user.

        Returns:
            Structured prompt text.
        """
        return self.build(task_text)
