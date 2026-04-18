from typing import List

from storage.entity.generate_message_entity import GenerateMessageEntity
import json

class PayloadContext:
    def __init__(self, generate_message_entity_list:List[GenerateMessageEntity] = None):
        self.required_reservation_id_constraint = False
        self.required_id_token_constraint = False
        self.generate_message_entity_list = generate_message_entity_list if generate_message_entity_list is not None else []
        self.event_type = None
        self.force_event_type = None
        self.force_remove_id_token = False
        self.trigger_reason = None
        self.variable_map = {}
        self.once_per_transaction_map = {}
        self.ev_connection_trigger_reason_list = [
            "CablePluggedIn"
        ]
        self.ev_connection_trigger = False
        self.force_trigger_reason = None


    def sent_public_key(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest":
                payload_dict = generate_message_entity.get_payload_dict()
                if self.contains_public_key(payload_dict):
                    return True
        return False
    def set_force_trigger_reason(self, reason):
        self.force_trigger_reason = reason

    def get_started_id_token(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest" :
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "idToken" in payload and payload["idToken"] is not None and payload["eventType"] == "Started":
                        return payload["idToken"]
                except json.JSONDecodeError:
                    continue
        return False


    def contains_public_key(self, obj):
        if isinstance(obj, dict):
            if "publicKey" in obj and obj["publicKey"]:
                return True
            return any(self.contains_public_key(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(self.contains_public_key(item) for item in obj)
        return False

    def set_variable_data_list(self, variable_data_list):
        for variable_data in variable_data_list:
            self.variable_map[(variable_data["component"]["name"], variable_data["variable"]["name"])] = variable_data["attributeValue"]

    def get_variable_value(self, component_name, variable_name):
        return self.variable_map.get((component_name, variable_name))

    def set_event_type(self, event_type):
        self.event_type = event_type

    def refresh(self):
        self.event_type = None
        self.trigger_reason = None

    def get_trigger_reason(self, values):
        if "ChargingStateChanged" in values and self.trigger_reason == "ChargingStateChanged":
            return "ChargingStateChanged"
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action in values:
                return generate_message_entity.action

    def get_provided_in_id(self, message_name):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == message_name:
                payload_dict = generate_message_entity.get_payload_dict()
                if message_name == "RequestStartTransactionRequest":
                    return payload_dict["remoteStartId"]
                else:
                    return payload_dict["requestId"]

    def is_stopped_by_request_stop_transaction_request(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "RequestStopTransactionRequest":
                return True
        return False

    def certificate_type_provided_in_sign_request(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "SignCertificateRequest" :
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "certificateType" in payload and payload["certificateType"] is not None:
                        return True
                except json.JSONDecodeError:
                    continue
        return False

    def get_saved_transaction_id(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest":
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "transactionInfo" in payload and payload["transactionInfo"] is not None:
                        if "transactionId" in payload["transactionInfo"] and  payload["transactionInfo"]["transactionId"] is not None:
                            return payload["transactionInfo"]["transactionId"]
                except json.JSONDecodeError:
                    continue
        return None

    def set_trigger_reason(self, trigger_reason):
        self.trigger_reason = trigger_reason

    def is_trigger_by_trigger_message_request(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TriggerMessageRequest":
                return True
        return False

    def get_stopped_by_message(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action in ["RequestStopTransactionRequest", "ResetRequest"]:
                return generate_message_entity.action
        return None

    def is_first_transaction(self):
        return not any(
            e.action == "TransactionEventRequest"
            for e in self.generate_message_entity_list
        )

    def set_force_event_type(self, event_type):
        self.force_event_type = event_type

    def set_force_remove_id_token(self):
        self.force_remove_id_token = True

    def set_ev_connection_trigger(self, ev_connection_trigger):
        self.ev_connection_trigger = ev_connection_trigger
    def required_reservation_id(self):
        self.required_reservation_id_constraint = True

    def required_id_token(self):
        self.required_id_token_constraint = True

    def firmware_update_ongoing(self):
        ongoing = False
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "FirmwareStatusNotificationRequest":
                ongoing = True
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "status" in payload and payload["status"] is not None:
                        if payload["status"] == "Installed":
                            return False
                except json.JSONDecodeError:
                    continue
        return ongoing


    def has_sent_public_key_before(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest":
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "meterValue" in payload and payload["meterValue"] is not None:
                        for meter_value in payload["meterValue"]:
                            if "sampledValue" in meter_value:
                                for sampled_value in meter_value["sampledValue"]:
                                    if "signedMeterValue" in sampled_value and sampled_value["signedMeterValue"] is not None:
                                        if "publicKey" in sampled_value["signedMeterValue"] and sampled_value["signedMeterValue"]["publicKey"] is not None:
                                            return "true"
                except json.JSONDecodeError:
                    continue
        return "false"

    def get_reservation_id(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "ReserveNowRequest":
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "id" in payload and payload["id"] is not None:
                        return payload["id"]
                except json.JSONDecodeError:
                    return None
        return None





    def is_first_transaction_event_with_reservation_id(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest":
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "reservationId" in payload and payload["reservationId"] is not None:
                        return False
                except json.JSONDecodeError:
                    continue
        return True

    def is_first_transaction_event_after_ev_connection_equal_true(self, trigger_reason):
        if trigger_reason in self.ev_connection_trigger_reason_list:
            return False
        return self.exist_ev_connection()

    def exist_ev_connection(self):
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "TransactionEventRequest":
                try:
                    payload = json.loads(generate_message_entity.payload)
                    if "triggerReason" in payload and payload["triggerReason"] in self.ev_connection_trigger_reason_list:
                        return False
                    if "evse" in payload and payload["evse"] is not None:
                        return False
                except json.JSONDecodeError:
                    continue
        return True

    def is_first_transaction_event_after_authorization(self):
        authorized_seen = False
        for generate_message_entity in self.generate_message_entity_list:
            if generate_message_entity.action == "AuthorizeRequest":
                authorized_seen = True
            elif generate_message_entity.action == "TransactionEventRequest" and authorized_seen:
                return False
        return True



