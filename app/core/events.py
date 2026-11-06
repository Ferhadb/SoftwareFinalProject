"""Event bus (Observer pattern, LC07).

Publishers do not know who listens. A failing handler is logged and never
breaks the publisher (e.g. a budget-alert bug must not fail an expense request).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExpenseCreated:
    user_id: int
    category: str  # a Category value; kept as str so core does not import models
    month: str  # "YYYY-MM"


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        for handler in self._handlers[type(event)]:
            try:
                handler(event)
            except Exception:
                log.exception("event handler %r failed for %r", handler, event)


bus = EventBus()
