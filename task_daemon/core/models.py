from pydantic import BaseModel
from typing import Any, Dict, Optional
from abc import ABC


class TaskInput(BaseModel, ABC):
    """Base class for all task input models"""

    pass


class TaskResult(BaseModel):
    """Standard task result model"""

    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Built-in task models
class SendEmailInput(TaskInput):
    recipient: str
    subject: str
    body: Optional[str] = None
    sender: Optional[str] = None


class ProcessDataInput(TaskInput):
    data: Dict[str, Any]
    operation: str = "process"


class UserSignupInput(TaskInput):
    email: str
    user_id: int
    metadata: Optional[Dict[str, Any]] = None
