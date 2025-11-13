from datetime import datetime
from pydantic import BaseModel


class SendEmailInput(BaseModel):
    recipient: str


class SendEmailOutput(BaseModel):
    sent_at: datetime


class LogAnalytics(BaseModel):
    event: str
