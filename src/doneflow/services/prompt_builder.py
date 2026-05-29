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
            A PT-BR prompt with RF-03 criteria and strict JSON output guidance.
        """
        return f"""
Você é um classificador de tarefas usando a Matriz de Eisenhower.

Analise a tarefa abaixo considerando os critérios de urgência e importância (RF-03):
- Urgência: sinais de tempo curto, pressão imediata, consequências de atraso.
- Importância: impacto estratégico, alinhamento com objetivos, valor de longo prazo.
- Impacto e consequências: avalie impacto no negócio, no cliente e no resultado esperado.
- Contexto profissional vs. pessoal e verbos de ação.

Palavras-chave de urgência a considerar:
- hoje, urgente, deadline, agora, prazo, cliente, entrega

Palavras-chave de importância estratégica a considerar:
- roadmap, produto, estratégia, proposta, reunião, CEO

Quadrantes possíveis (use exatamente estes nomes):
- DO_NOW: urgente e importante
- SCHEDULE: não urgente e importante
- DELEGATE: urgente e não importante
- ELIMINATE: não urgente e não importante

Tarefa:
"{task_text}"

Responda APENAS em JSON válido (sem markdown, sem texto extra), no formato:
{{
  "quadrant": "DO_NOW|SCHEDULE|DELEGATE|ELIMINATE",
  "confidence": 0.0,
  "reasoning": "explicação curta em PT-BR"
}}

Regras de saída:
- "quadrant" deve ser um dos 4 valores exatos.
- "confidence" deve ser número entre 0.0 e 1.0.
- "reasoning" deve ser string em português (PT-BR).
""".strip()

    def build_prompt(self, task_text: str) -> str:
        """Backward-compatible wrapper for prompt generation.

        Args:
            task_text: Raw task description provided by the user.

        Returns:
            Structured prompt text.
        """
        return self.build(task_text)
