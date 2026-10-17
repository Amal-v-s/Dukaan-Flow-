"""Request-local active tenant scope."""
from contextvars import ContextVar

_business_id: ContextVar[str] = ContextVar("dukaanflow_business_id", default="biz_demo_kirana")
_user_id: ContextVar[str] = ContextVar("dukaanflow_user_id", default="user_demo")
_write_batch: ContextVar[object | None] = ContextVar("dukaanflow_write_batch", default=None)


def set_business_id(business_id: str):
    return _business_id.set(business_id)


def get_business_id() -> str:
    return _business_id.get()


def reset_business_id(token) -> None:
    _business_id.reset(token)


def set_user_id(user_id: str):
    return _user_id.set(user_id)


def get_user_id() -> str:
    return _user_id.get()


def reset_user_id(token) -> None:
    _user_id.reset(token)


def set_write_batch(batch):
    return _write_batch.set(batch)


def get_write_batch():
    return _write_batch.get()


def reset_write_batch(token) -> None:
    _write_batch.reset(token)
