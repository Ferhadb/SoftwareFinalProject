from app.core.events import EventBus, ExpenseCreated

E = ExpenseCreated(user_id=1, category="Food", month="2026-11")


def test_publish_calls_subscribers_in_order():
    bus, seen = EventBus(), []
    bus.subscribe(ExpenseCreated, lambda e: seen.append(("a", e)))
    bus.subscribe(ExpenseCreated, lambda e: seen.append(("b", e)))
    bus.publish(E)
    assert seen == [("a", E), ("b", E)]


def test_publish_without_subscribers_is_noop():
    EventBus().publish(E)


def test_other_event_types_are_ignored():
    bus, seen = EventBus(), []
    bus.subscribe(int, seen.append)
    bus.publish(E)
    assert seen == []


def test_failing_handler_does_not_break_others(caplog):
    bus, seen = EventBus(), []

    def boom(_):
        raise RuntimeError("x")

    bus.subscribe(ExpenseCreated, boom)
    bus.subscribe(ExpenseCreated, seen.append)
    bus.publish(E)
    assert seen == [E]
    assert "failed" in caplog.text
