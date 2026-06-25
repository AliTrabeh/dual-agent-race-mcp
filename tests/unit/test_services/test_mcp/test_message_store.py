from hw6_race.services.mcp.message_store import MessageStore


def test_send_appends_to_outbox_log() -> None:
    store = MessageStore()
    store.send("hello from cop")
    assert store.outbox_log() == ["hello from cop"]


def test_receive_then_drain_returns_messages_in_order() -> None:
    store = MessageStore()
    store.receive("first")
    store.receive("second")
    assert store.drain_inbox() == ["first", "second"]


def test_drain_inbox_clears_the_inbox() -> None:
    store = MessageStore()
    store.receive("only once")
    store.drain_inbox()
    assert store.drain_inbox() == []


def test_outbox_log_is_not_affected_by_drain_inbox() -> None:
    store = MessageStore()
    store.send("outgoing")
    store.receive("incoming")
    store.drain_inbox()
    assert store.outbox_log() == ["outgoing"]


def test_outbox_log_returns_a_copy_not_a_live_reference() -> None:
    store = MessageStore()
    store.send("outgoing")
    log = store.outbox_log()
    log.append("mutated externally")
    assert store.outbox_log() == ["outgoing"]


def test_drain_outbox_one_returns_oldest_and_removes_it() -> None:
    store = MessageStore()
    store.send("first")
    store.send("second")
    assert store.drain_outbox_one() == "first"
    assert store.drain_outbox_one() == "second"


def test_drain_outbox_one_returns_none_when_outbox_is_empty() -> None:
    store = MessageStore()
    assert store.drain_outbox_one() is None
