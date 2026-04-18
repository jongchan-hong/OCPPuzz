from enum import Enum, auto

from dto.constraint_collect_dto import Condition, Rule


class ConditionEnum(Enum):
    PROVIDED_EQUAL_FALSE = auto()
    PROVIDED_EQUAL_TRUE = auto()
    VALUE_EQUAL = auto()
    TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST = auto()
    NOT_TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST = auto()
    VALUE_IN = auto()
    MESSAGE_TYPE_NOT_EQUAL = auto()
    VALUE_NOT_EQUAL = auto()
    UNKNOWN_FIELD = auto()
    IMPLEMENTED_EQUAL = auto()
    STATUS_EQUAL_CHANGED = auto()
    NOT_EMPTY_EQUAL_TRUE = auto()
    MESSAGE_TYPE_EQUAL = auto()
    EXIST_EQUAL_FALSE = auto()
    IS_FIRST_TRANSACTION_EVENT_AFTER_EV_CONNECTION_EQUAL_FALSE = auto()
    IS_FIRST_TRANSACTION_EVENT_AFTER_AUTHORIZATION_EQUAL_FALSE = auto()
    IS_FIRST_TRANSACTION = auto()
    STOPPED_BY_REQUEST_STOP_TRANSACTION_REQUEST = auto()
    CONTEXT_CERTIFICATES_STATUS =auto()
    CONTEXT_NUMBER_PHASES_NOT_PROVIDED = auto()
    PROVIDED_CERTIFICATE_TYPE = auto()
    CHARGING_PROFILE_PURPOSE_IN = auto()
    CONTEXT_TRANSACTION_EVENT_REQUEST_CONTAINS_EQUAL = auto()
    CERTIFICATE_TYPE_PROVIDED_IN_SIGN_REQUEST = auto()
    UNTESTABLE_CONDITION = auto()



class ConditionDefine(object):
    PASS_LIST = [
        ConditionEnum.UNTESTABLE_CONDITION
    ]

    @staticmethod
    def isPassCondition(rule: Rule):
        if not rule.conditions:
            return False
        for condition in rule.conditions:
            condition_enum = ConditionDefine.getConditionEnum(condition)
            if condition_enum is None:
                print("@@ unknown condition type::")
                print(condition)
                print(rule)
                return True
            if condition_enum in ConditionDefine.PASS_LIST:
                return True
        return False

    @staticmethod
    def getConditionEnum(condition: Condition):
        if condition.attribute == "bothConnectionsImplemented":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "loggingInformationAvailable":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "resultSet":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "firmwareUpdateOngoing":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "logUploadOngoing":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "optional":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.target and "transmittedValue" in condition.target:
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "values" and condition.target == "context.certificateType" and condition.operator == "equal" and "last" in condition.values:
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.target == "triggeredBy":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.target == "context.stateChanged":
            return ConditionEnum.UNTESTABLE_CONDITION
        if condition.attribute == "provided" and condition.operator == "equal":
            if "false" in condition.values:
                return ConditionEnum.PROVIDED_EQUAL_FALSE
            if "true" in condition.values:
                return ConditionEnum.PROVIDED_EQUAL_TRUE
        if condition.attribute in ["values", "value"] and condition.operator == "equal":
            return ConditionEnum.VALUE_EQUAL
        if condition.attribute == "isFirstTransactionEventAfterEVConnection" and condition.operator == "equal" and "false" in condition.values:
            return ConditionEnum.IS_FIRST_TRANSACTION_EVENT_AFTER_EV_CONNECTION_EQUAL_FALSE
        if condition.attribute == "isFirstTransactionEventAfterAuthorization" and condition.operator == "equal" and "false" in condition.values:
            return ConditionEnum.IS_FIRST_TRANSACTION_EVENT_AFTER_AUTHORIZATION_EQUAL_FALSE
        if condition.target == "context.isFirstTransaction" and condition.attribute == "values" and condition.operator == "equal" and "true" in condition.values:
            return ConditionEnum.IS_FIRST_TRANSACTION
        if condition.attribute == "triggeredBy" and condition.operator == "equal" and "TriggerMessageRequest" in condition.values:
            return ConditionEnum.TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST
        if condition.attribute == "triggeredBy" and condition.operator == "notEqual" and "TriggerMessageRequest" in condition.values:
            return ConditionEnum.NOT_TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST
        if condition.attribute in ["value", "values"] and condition.operator == "in":
            return ConditionEnum.VALUE_IN
        if condition.attribute == "messageType" and condition.operator == "notEqual":
            return ConditionEnum.MESSAGE_TYPE_NOT_EQUAL
        if condition.attribute in ["values", "value"] and condition.operator == "notEqual":
            return ConditionEnum.VALUE_NOT_EQUAL
        if condition.attribute == "implemented":
            return ConditionEnum.IMPLEMENTED_EQUAL
        if condition.attribute == "status"  and condition.operator == "equal" and "changed" in condition.values:
            return ConditionEnum.STATUS_EQUAL_CHANGED
        if condition.attribute == "notEmpty" and condition.operator == "equal" and "true" in condition.values:
            return ConditionEnum.NOT_EMPTY_EQUAL_TRUE
        if condition.attribute == "messageType" and condition.operator == "equal":
            return ConditionEnum.MESSAGE_TYPE_EQUAL
        if condition.attribute == "exist" and condition.operator == "equal" and "false" in condition.values:
            return ConditionEnum.EXIST_EQUAL_FALSE
        if condition.attribute == "stoppedBy" and condition.operator == "equal" and "RequestStopTransactionRequest" in condition.values:
            return ConditionEnum.STOPPED_BY_REQUEST_STOP_TRANSACTION_REQUEST
        if condition.target == "context.certificates" and condition.attribute == "status":
            return ConditionEnum.CONTEXT_CERTIFICATES_STATUS
        if condition.target == "context" and condition.attribute == "numberPhases"and condition.operator == "notEqual" and "provided" in condition.values:
            return ConditionEnum.CONTEXT_NUMBER_PHASES_NOT_PROVIDED

        if condition.target == "context" and condition.attribute == "certificateType" and condition.operator == "provided" and 'true' in condition.values:
            return ConditionEnum.PROVIDED_CERTIFICATE_TYPE
        if condition.target =="context.transactionEventRequest" and condition.attribute == "contains" and condition.operator == "equal":
            return ConditionEnum.CONTEXT_TRANSACTION_EVENT_REQUEST_CONTAINS_EQUAL

        if condition.attribute == "ChargingProfilePurpose" and condition.operator in ["equal", "in"]:
            return ConditionEnum.CHARGING_PROFILE_PURPOSE_IN

        if condition.attribute == "certificateType" and condition.target == "context.SignCertificateRequest" and condition.operator == "provided":
            return ConditionEnum.CERTIFICATE_TYPE_PROVIDED_IN_SIGN_REQUEST



        print(f"unknown condition Enum {condition}")

        return None