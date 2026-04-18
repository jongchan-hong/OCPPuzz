from dataclasses import dataclass
from pydantic import BaseModel
class InstructionMessageDTO(BaseModel):
    role: str
    content: str