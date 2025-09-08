from .generators import mckay_wormald as _mckay_wormald
from .generators.mckay_wormald import *  # noqa: F403

__all__ = list(
    getattr(_mckay_wormald, "__all__", [n for n in dir(_mckay_wormald) if not n.startswith("_")])
)
