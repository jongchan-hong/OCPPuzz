from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ValidationError

class AdditionalInfoDTO(BaseModel):
    reference_message: Optional[str] = None

class MessageDirectionDTO(BaseModel):
    from_: List[str] = Field(alias="from")
    to: List[str]
    additional_info_required: Optional[AdditionalInfoDTO] = None