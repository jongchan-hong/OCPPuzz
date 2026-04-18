from typing import Optional
from dataclasses import dataclass
@dataclass
class GPTRetryDTO:
    retry: int
    error_content: str
    exception: Optional[Exception] = None