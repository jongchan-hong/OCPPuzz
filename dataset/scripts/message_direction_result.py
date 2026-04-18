import os
import json
from pydantic import BaseModel, validator
from typing import List, Union, Optional


class MessageDirection(BaseModel):
    message_name: str
    caller: Union[str, List[str]]
    callee: Union[str, List[str]]

    @validator("caller", "callee", pre=True)
    def convert_to_list(cls, value):
        if isinstance(value, str):
            return [value] if value else []
        return value

class MessageDirectionResult:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_PATH = os.path.join(BASE_DIR, "message_direction_result.json")
    pass_list = [
        "Get15118EVCertificateRequest",
        "NotifyEVChargingNeedsRequest",
        "NotifyEVChargingScheduleRequest"
    ]

    def __init__(self):
        self.data = self.load()
        self.message_directions: List[MessageDirection] = [MessageDirection(**item) for item in self.data]

    def load(self):
        with open(self.FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_target_request_detail_list(self) -> List[str]:
        return [
            md.message_name for md in self.message_directions
            if "CSMS" in md.callee and md.message_name.endswith("Request")
        ]
    def get_random_test_message_list(self) -> List[str]:
        return [
            md.message_name for md in self.message_directions
            if "CSMS" in md.callee and md.message_name.endswith("Request") and md.message_name not in self.pass_list
        ]

    def find_by_message_name(self, message_name: str) -> Optional[MessageDirection]:
        for md in self.message_directions:
            if md.message_name == message_name:
                return md
        return None