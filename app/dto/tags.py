
from pydantic import BaseModel


class TagCreatePayload(BaseModel):
    userIdLine: str
    name: str
