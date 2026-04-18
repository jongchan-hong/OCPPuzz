from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import relationship

from constants.version_config import version201
from storage.entity.base_entity import Base
from util.hash import calculate_sha256
from storage.entity.gpt_message_direction_log_entity import GPTMessageDirectionLogEntity
from storage.entity.message_direction_detail_entity import MessageDirectionDetailEntity
from storage.entity.message_direction_fail_entity import MessageDirectionFailEntity


class MessageDirectionEntity(Base):
    __tablename__ = "message_direction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    file_path = Column(String(255), nullable=False)
    check_sum_hash = Column(String(255), nullable=False, default="")

    detail_list = relationship(MessageDirectionDetailEntity, back_populates="message_direction_entity", cascade="all, delete-orphan")
    fail_list = relationship(MessageDirectionFailEntity, back_populates="message_direction_entity", cascade="all, delete-orphan")
    log_list = relationship(GPTMessageDirectionLogEntity, back_populates="message_direction_entity", cascade="all, delete-orphan")

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.check_sum_hash = calculate_sha256(file_path)

    def get_scenario_collect_instructions(self):
        result = []
        for message_direction_detail in self.detail_list:
            data = {
                "message_name": message_direction_detail.action,
                "caller": [from_entity.from_value for from_entity in message_direction_detail.from_list],
                "callee": [to_entity.to_value for to_entity in message_direction_detail.to_list],
            }
            if message_direction_detail.action == "GetVariablesResponse":
                data["caller"] = "Charging Station"
                data["callee"] = "CSMS"
            result.append(data)

        for message_direction_fail_entity in self.fail_list:
            if message_direction_fail_entity.message == "NotifyCustomerInformationRequest":
                result.append(
                    {
                        "message_name": message_direction_fail_entity.message,
                        "caller": "Charging Station",
                        "callee": "CSMS",
                    }
                )
            else:
                result.append(
                    {
                        "message_name": message_direction_fail_entity.message,
                        "caller": "",
                        "callee": "",
                    }
                )
        return result

    def get_target_request_action_list(self, target_system:str):
        result = []
        for message_direction_detail in self.detail_list:
            for to_entity in message_direction_detail.to_list:
                if (target_system == to_entity.to_value and
                        (message_direction_detail.action.endswith("Request") or message_direction_detail.action.endswith(".req"))
                ):
                    result.append(message_direction_detail.action)
        if self.file_path == version201.document_path:
            result.append("NotifyCustomerInformationRequest")
        return result