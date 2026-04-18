import random

from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from storage.entity.base_entity import BaseEntity, session
from sqlalchemy import Column, String, Integer, ForeignKey
import json

from storage.entity.test_execution_entity import TestExecutionEntity
from exception.uncreatable_value_exception import UncreatableValueException
from dateutil import parser
from datetime import datetime, timedelta, timezone


class GenerateMessageEntity(BaseEntity):
    __tablename__ = 'generate_message'

    message_type_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    payload = Column(LONGTEXT, nullable=False)

    generate_rule_combination_id = Column(Integer, ForeignKey('generate_rule_combination.id'))
    generate_rule_combination_entity = relationship("GenerateRuleCombinationEntity", back_populates="generate_message_list")

    test_id = Column(Integer, ForeignKey("test.id"))
    test_entity = relationship("TestEntity", back_populates="generate_message_list")

    scenario_test_detail_set_id = Column(Integer, ForeignKey("scenario_test_detail_set.id"))
    scenario_test_detail_set_entity = relationship("ScenarioTestDetailSetEntity", back_populates="generate_message_list")


    test_execution_list = relationship(
        argument=TestExecutionEntity,
        back_populates="generate_message_entity",
        cascade="all, delete-orphan"
    )

    send_trigger_entity = relationship(
        argument="SendTriggerEntity",
        back_populates="generate_message_entity",
        uselist=False
    )

    def patch_payload(self, context, test = False):
        dict = self.get_payload_dict()
        match self.action:
            case "SetChargingProfile":
                if "evseId" in dict:
                    if dict["evseId"] < 0:
                        dict["evseId"] *= -1

                if dict["chargingProfile"]["stackLevel"] < 0:
                    dict["chargingProfile"]["stackLevel"] *= -1

                if "chargingProfilePurpose" in dict["chargingProfile"]:
                    if dict["chargingProfile"]["chargingProfilePurpose"] == "ChargingStationExternalConstraints":
                        dict["chargingProfile"]["chargingProfilePurpose"] = random.choice(
                            [
                                "ChargingStationMaxProfile",
                                "TxDefaultProfile",
                                "TxProfile"
                            ]
                        )
                    if dict["chargingProfile"]["chargingProfilePurpose"] == "ChargingStationMaxProfile":
                        dict["evseId"] = 0

                if dict["chargingProfile"]["chargingProfilePurpose"] == "ChargingStationMaxProfile" and dict["chargingProfile"]["chargingProfileKind"] == "Relative":
                    dict["chargingProfile"]["chargingProfileKind"] = random.choice(["Recurring","Absolute"])


                if dict["chargingProfile"]["chargingProfilePurpose"] == "TxProfile":
                    transaction_id = context.get_saved_transaction_id()
                    if not transaction_id:
                        transaction_id = "temp-transaction-id"
                        if not test:
                            raise UncreatableValueException("TxProfile Must Have Transaction ID")
                    dict["chargingProfile"]["transactionId"] = transaction_id
                schedules = dict["chargingProfile"].get("chargingSchedule", [])
                for schedule in schedules:
                    periods = schedule.get("chargingSchedulePeriod", [])
                    for period in periods:
                        limit = period.get("limit")
                        if isinstance(limit, str):
                            try:
                                limit = float(limit)
                            except ValueError:
                                continue
                        if isinstance(limit, (int, float)):
                            period["limit"] = round(limit, 1)
                if "validTo" in dict["chargingProfile"]:
                    parsed_time = parser.isoparse(dict["chargingProfile"]["validTo"])
                    now = datetime.now(parsed_time.tzinfo)
                    if parsed_time < now:
                        new_time = now + timedelta(weeks=1)
                        dict["chargingProfile"]["validTo"] = new_time.isoformat()
                if "chargingSchedule" in dict["chargingProfile"]:
                    for i in range(len(dict["chargingProfile"]["chargingSchedule"])):
                        dict["chargingProfile"]["chargingSchedule"][i]["chargingSchedulePeriod"][0]["startPeriod"] = 0
                if "chargingProfileKind" in dict["chargingProfile"]:
                    for i in range(len(dict["chargingProfile"]["chargingSchedule"])):
                        if not "startSchedule" in dict["chargingProfile"]["chargingSchedule"][i]:
                            if dict["chargingProfile"]["chargingProfileKind"] in ["Absolute", "Recurring"]:
                                now = datetime.now(timezone.utc) + timedelta(weeks=1)
                                dict["chargingProfile"]["chargingSchedule"][i]["startSchedule"] = now.isoformat()
                        else:
                            if dict["chargingProfile"]["chargingProfileKind"] == "Relative":
                                del dict["chargingProfile"]["chargingSchedule"][i]["startSchedule"]
            case "ReserveNowRequest":
                if "evseId" in dict:
                    if dict["evseId"] < 0:
                        dict["evseId"] *= -1
            case "RequestStartTransactionRequest":
                if "evseId" in dict:
                    if dict["evseId"] < 0:
                        dict["evseId"] *= -1
                if "chargingProfile" in dict:
                    if "stackLevel" in dict["chargingProfile"]:
                        if dict["chargingProfile"]["stackLevel"] < 0:
                            dict["chargingProfile"]["stackLevel"] *= -1
                pass
            case "GetChargingProfilesRequest":
                if "chargingProfileId" in dict["chargingProfile"]:
                    dict["chargingProfile"].pop("chargingProfilePurpose", None)
                    dict["chargingProfile"].pop("stackLevel", None)
                    dict["chargingProfile"].pop("chargingLimitSource", None)
                pass
            case "CancelReservationRequest":
                reservation_id = context.get_reservation_id()
                if reservation_id is not None:
                    dict["reservationId"] = reservation_id
        self.payload = json.dumps(dict, ensure_ascii=False)
        session.commit()

        if "evseId" in dict:
            return dict["evseId"]
        return None

    def get_payload_dict(self):
        try:
            parsed_payload = json.loads(self.payload)
            return parsed_payload
        except json.JSONDecodeError as e:
            import traceback
            traceback.print_exc()
            return None

    def get_call_json(self):
        return json.dumps([
            self.message_type_id,
            str(self.id),
            self.action.removesuffix("Request"),
            self.get_payload_dict()
        ], ensure_ascii=False)

    def get_call_result_json(self):
        return json.dumps([
            self.message_type_id,
            str(self.id),
            self.get_payload_dict()
        ], ensure_ascii=False)


