"""Task handler decorators."""

from typing import Dict, Callable
from functools import wraps
from pydantic import BaseModel

# Registry for task handlers
_task_handlers: Dict[str, Callable[[BaseModel], BaseModel]] = {}


def task_handler(func: Callable[[BaseModel], BaseModel]) -> Callable[[BaseModel], BaseModel]:
    """
    Decorator to register a task handler using function name as task type.

    Handler can accept any input and return any output (like AWS Lambda).
    """

    @wraps(func)
    def wrapper(event: BaseModel) -> BaseModel:
        return func(event)

    task_type = func.__name__
    _task_handlers[task_type] = wrapper
    return wrapper


def get_task_handler(task_type: str) -> Callable[[BaseModel], BaseModel]:
    """Get registered task handler by type."""
    return _task_handlers.get(task_type)


def get_all_handlers() -> Dict[str, Callable[[BaseModel], BaseModel]]:
    """Get all registered task handlers."""
    return _task_handlers.copy()


def clear_handlers():
    """Clear all registered handlers (for testing)."""
    _task_handlers.clear()
