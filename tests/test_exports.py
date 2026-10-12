import pytest

import seg


def test_every_exported_attribute_is_accessible() -> None:
    for attr in dir(seg):
        getattr(seg, attr)


@pytest.mark.parametrize("symbol", ["Completion", "ChatCompletion", "Audio", "FineTune", "Customer", "Engine"])
def test_legacy_openai_symbols_are_not_exported(symbol: str) -> None:
    assert not hasattr(seg, symbol)
