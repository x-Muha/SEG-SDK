from __future__ import annotations

import array
import base64
from typing import List, Optional

from .._extras import numpy as np, has_numpy


def decode_base64_embedding(data: str, *, use_numpy: Optional[bool] = None) -> List[float]:
    """Decode a base64-encoded float32 vector, as returned for `encoding_format="base64"`.

    `use_numpy` lets a caller that decodes many vectors check for numpy once; by default
    the check happens here.
    """
    raw = base64.b64decode(data)
    if has_numpy() if use_numpy is None else use_numpy:
        return np.frombuffer(raw, dtype="float32").tolist()  # type: ignore[no-untyped-call, no-any-return]
    return array.array("f", raw).tolist()
