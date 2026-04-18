from typing import Optional
from typing import List
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class GPTRunResultDTO:
    response: str

class MessageDTO(BaseModel):
    role: str
    content: str

@dataclass
class RequestInfoDTO(BaseModel):
    messages: List[MessageDTO]
    model: str
    timeout: int