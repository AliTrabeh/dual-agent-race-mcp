from hw6_race.services.agents.llm_providers import AnthropicCompleteFn


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class _FakeMessagesResource:
    def __init__(self, reply_text: str) -> None:
        self.reply_text = reply_text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeMessage(self.reply_text)


class _FakeAnthropicClient:
    def __init__(self, reply_text: str = "2,3") -> None:
        self.messages = _FakeMessagesResource(reply_text)


def test_complete_fn_returns_the_response_text_stripped() -> None:
    fake_client = _FakeAnthropicClient(reply_text="  UNKNOWN  ")
    complete = AnthropicCompleteFn("fake-key", model="claude-haiku-4-5", client=fake_client)

    result = complete("some prompt")

    assert result == "UNKNOWN"


def test_complete_fn_sends_the_prompt_as_a_user_message() -> None:
    fake_client = _FakeAnthropicClient()
    complete = AnthropicCompleteFn("fake-key", client=fake_client)

    complete("describe your situation")

    sent = fake_client.messages.calls[0]
    assert sent["messages"] == [{"role": "user", "content": "describe your situation"}]


def test_complete_fn_uses_the_configured_model_and_a_small_max_tokens() -> None:
    fake_client = _FakeAnthropicClient()
    complete = AnthropicCompleteFn("fake-key", model="claude-sonnet-4-6", client=fake_client)

    complete("hello")

    sent = fake_client.messages.calls[0]
    assert sent["model"] == "claude-sonnet-4-6"
    assert sent["max_tokens"] <= 100


def test_complete_fn_defaults_to_haiku_when_no_model_given() -> None:
    fake_client = _FakeAnthropicClient()
    complete = AnthropicCompleteFn("fake-key", client=fake_client)

    complete("hello")

    assert fake_client.messages.calls[0]["model"] == "claude-haiku-4-5"
