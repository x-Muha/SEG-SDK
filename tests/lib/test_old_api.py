import pytest

import seg
from seg.lib._old_api import APIRemovedInV1


def test_basic_attribute_access_works() -> None:
    for attr in dir(seg):
        getattr(seg, attr)


def test_helpful_error_is_raised() -> None:
    with pytest.raises(APIRemovedInV1):
        seg.Completion.create()  # type: ignore

    with pytest.raises(APIRemovedInV1):
        seg.ChatCompletion.create()  # type: ignore
