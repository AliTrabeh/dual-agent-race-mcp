"""Real LLM provider complete_fn implementations, usable as any
GatekeptLLMClient backend (HW-F19). Kept separate from llm_client.py so
adding more providers later doesn't grow that file — each provider's wire
format lives in its own small callable.
"""

import anthropic

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"
DEFAULT_MAX_TOKENS = 64


class AnthropicCompleteFn:
    """Setup: api_key, model, and an optional injected client (for tests).
    Input: a prompt string. Output: the model's text reply, stripped.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_ANTHROPIC_MODEL,
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self._client = client or anthropic.Anthropic(api_key=api_key)
        self._model = model

    def __call__(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=DEFAULT_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
