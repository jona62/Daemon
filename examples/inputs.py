from pydantic import BaseModel


class SendEmailInput(BaseModel):
    recipient: str


class LogAnalytics(BaseModel):
    event: str
