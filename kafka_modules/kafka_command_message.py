from dataclasses import dataclass

import json
from typing_extensions import Optional
from enum import Enum


from generator_modules.fix_value_container import FixValueContainer
from constants.ocpp_version import OcppVersion


class KafkaCommandEnum(Enum):
    RANDOM = "random"
    RULE_BASED_RANDOM = "rule based random"
    RULE_BASED_SCENARIO = "rule based scenario"


@dataclass
class KafkaCommandMessage:
    command: KafkaCommandEnum
    ocpp_version: OcppVersion
    gen_cnt:Optional[int]

    @staticmethod
    def from_json(json_str: str):
        try:
            data = json.loads(json_str)
            return KafkaCommandMessage(
                command=KafkaCommandEnum(data["command"]),
                ocpp_version = OcppVersion(data["ocpp_version"]),
                gen_cnt = data.get("gen_cnt")
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"[Error] JSON Parse Fail: {e}")
            return None

    def to_json(self):
        return json.dumps({
            "command": self.command.value,
            "ocpp_version": self.ocpp_version.value,
            "gen_cnt": self.gen_cnt
        })