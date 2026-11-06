from app.core.monads import Maybe, Writer

f = lambda x: Maybe.of(x + 1)
g = lambda x: Maybe.of(x * 2)


def test_maybe_none_is_nothing():
    assert Maybe.of(None).is_nothing()
    assert not Maybe.of(0).is_nothing()


def test_maybe_nothing_short_circuits():
    m = Maybe.nothing().map(lambda x: x + 1).bind(f)
    assert m.is_nothing()
    assert m.get_or_else(42) == 42


def test_maybe_map_and_bind():
    assert Maybe.of(1).map(lambda x: x + 1).get_or_else(0) == 2
    assert Maybe.of(1).bind(f) == Maybe.of(2)
    assert Maybe.of(1).bind(lambda _: Maybe.nothing()).is_nothing()


def test_maybe_laws():
    a = 3
    assert Maybe.of(a).bind(f) == f(a)  # left identity
    m = Maybe.of(a)
    assert m.bind(Maybe.of) == m  # right identity
    assert m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))  # associativity
    n = Maybe.nothing()
    assert n.bind(Maybe.of) == n


def w1(x):
    return Writer(x + 1, [f"inc {x}"])


def w2(x):
    return Writer(x * 2, [f"dbl {x}"])


def test_writer_tell_and_run():
    assert Writer.unit(5).tell("a").tell("b").run() == (5, ["a", "b"])


def test_writer_bind_concatenates_logs():
    assert Writer.unit(1).tell("start").bind(w1).bind(w2).run() == (
        4,
        ["start", "inc 1", "dbl 2"],
    )


def test_writer_laws():
    a = 3
    assert Writer.unit(a).bind(w1) == w1(a)  # left identity
    m = Writer(a, ["x"])
    assert m.bind(Writer.unit) == m  # right identity
    assert m.bind(w1).bind(w2) == m.bind(lambda x: w1(x).bind(w2))  # associativity


def test_writer_is_immutable():
    w = Writer.unit(1)
    w.tell("x")
    assert w.run() == (1, [])
