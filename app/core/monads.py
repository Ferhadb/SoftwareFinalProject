"""Maybe and Writer monads (LC08).

Maybe: a value or nothing, so pipelines never need None checks or exceptions.
Writer: a value plus a log, so each pipeline step can record what it did.
"""

from __future__ import annotations

from collections.abc import Callable


class Maybe[T]:
    def __init__(self, value: T | None, present: bool):
        self._value = value
        self._present = present

    @staticmethod
    def of(value: T | None) -> Maybe[T]:
        return Maybe(value, value is not None)

    @staticmethod
    def nothing() -> Maybe[T]:
        return Maybe(None, False)

    def map[U](self, f: Callable[[T], U]) -> Maybe[U]:
        return Maybe.of(f(self._value)) if self._present else Maybe.nothing()  # type: ignore[arg-type]

    def bind[U](self, f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return f(self._value) if self._present else Maybe.nothing()  # type: ignore[arg-type]

    def get_or_else(self, default: T) -> T:
        return self._value if self._present else default  # type: ignore[return-value]

    def is_nothing(self) -> bool:
        return not self._present

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Maybe)
            and self._present == other._present
            and self._value == other._value
        )

    def __repr__(self) -> str:
        return f"Just({self._value!r})" if self._present else "Nothing"


class Writer[T]:
    def __init__(self, value: T, log: list[str] | None = None):
        self._value = value
        self._log = list(log or [])

    @staticmethod
    def unit(value: T) -> Writer[T]:
        return Writer(value)

    def tell(self, message: str) -> Writer[T]:
        return Writer(self._value, [*self._log, message])

    def bind[U](self, f: Callable[[T], Writer[U]]) -> Writer[U]:
        nxt = f(self._value)
        return Writer(nxt._value, [*self._log, *nxt._log])

    def run(self) -> tuple[T, list[str]]:
        return self._value, list(self._log)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Writer) and self.run() == other.run()

    def __repr__(self) -> str:
        return f"Writer({self._value!r}, {self._log!r})"
