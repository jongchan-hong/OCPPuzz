from enum import Enum, auto

from dto.constraint_collect_dto import Constraint, Rule

class ConstraintEnum(Enum):
    MAX_LENGTH = auto()
    BYTES_FIX = auto()
    ENUM = auto()
    TYPE_EQUAL = auto()
    REQUIRED_EQUAL_TRUE = auto()
    REQUIRED_EQUAL_FALSE = auto()
    OPTIONAL_EQUAL_TRUE = auto()
    AGREED_UPON_BY_ALL_PARTIES = auto()
    FORMAT_EQUAL_HEX = auto()
    JAVA_TYPE_EQUAL = auto()
    ENCODING_EQUAL = auto()
    FORMAT_EQUAL = auto()
    FORMAT_EQUAL_UTF8 = auto()
    FORMAT_EQUAL_HUMAN_READABLE = auto()
    CASE_INSENSITIVE = auto()
    CASE_SENSITIVE = auto()
    VALUE_EQUAL_EMPTY_STRING = auto()
    VALUE_EQUAL = auto()
    VALUE_NOT_EQUAL = auto()
    MIN_ITEMS_EQUAL = auto()
    MAX_ITEMS_EQUAL = auto()
    NOT_LEADING_ZEROS = auto()
    PREFIX_NOT_EQUAL = auto()
    IMPLEMENTED_EQUAL_FALSE = auto()
    VALUE_FROM = auto()
    VALUE_GT = auto()
    VALUE_GE = auto()
    STATUS_EQUAL = auto()
    WAS_PROVIDED_IN = auto()
    SPEC_IN_ISO15118 = auto()
    SPEC_IN_RFC5646 = auto()
    DEFAULT_EQUAL = auto()
    DECIMAL_PLACES_MAX = auto()
    CHARACTER_SET_UTF8 = auto()
    CHARACTER_SET_IN = auto()
    BIT_EQUAL = auto()
    VALUE_FROM_MEASUREMENTS_APPENDICES = auto()
    VALUE_FROM_STANDARDIZED_COMPONENT_NAMES = auto()
    VALUE_FROM_STANDARDIZED_VARIABLE_NAMES = auto()
    VALUE_FROM_SECURITY_EVENTS_LIST = auto()
    VALUE_FROM_UNDEFINED = auto()
    REMOVE_FIELD_EQUAL_TRUE = auto()
    VALUE_BETWEEN = auto()
    MAX_ITEMS_EQUAL_MAX_SCHEDULE_TUPLES = auto()
    VALUE_IN_FALSE_AND_TRUE = auto()
    REPRESENTATION_EQUAL = auto()
    IMPLEMENTED_EQUAL_TRUE = auto()
    IMPLEMENTED_EQUAL_CUSTOM = auto()
    MAXIMUM_EQUAL = auto()
    MAX_LENGTH_EQUAL_MAX_LIMIT = auto()
    UNKNOWN_ATTRIBUTE = auto()
    CONFIGURATION_EQUAL = auto()
    VALUE_MAX_DURATION_OF_THE_TRANSACTION = auto()
    CONTENT_CONFIGURED_BY = auto()
    SENDING_DEPENDS_ON_EQUAL = auto()
    WAS_STORED_IN_CSMS = auto()
    CAN_VERIFICATION_EQUAL= auto()
    SIGNED_WITH_AND = auto()
    VALUE_MONITOR_VALUE = auto()
    ONCE_PER_TRANSACTION_EQUAL_TRUE = auto()
    ENCODING_EQUAL_UTF8 = auto()
    VARIABLE_EQUAL_HEART_BEAT_INTERVAL = auto()
    MINIMUM_EQUAL_TRUE = auto()
    VARIABLE_EQUAL_CURRENCY = auto()
    CHARGING_PROFILE_PURPOSE_EQUAL = auto()
    RELEVANT_EQUAL = auto()
    CERTIFICATE_TYPE_EQUAL = auto()
    UNTESTABLE_CONSTRAINT = auto()







class ConstraintDefine(object):

    @staticmethod
    def getConstraintEnum(constraint:Constraint):
        if constraint.attribute == "messageType":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "action":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "support":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "resultSet":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "report":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "priority":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "state":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "triggeredBy":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "loggingInformationAvailable":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "logUploadOngoing":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "transaction":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute == "specification":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute=='usage' and constraint.operator=='equal' and  "15118 and CSMS connection" in constraint.values:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute=='certificateType':
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute=='firmwareUpdateOngoing':
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if constraint.attribute.startswith("variable"):
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if "variable.TariffCostCtrlr.Currency" in constraint.values:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        if not constraint.values:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if (constraint.attribute == "value" or constraint.attribute == "values" ) and constraint.operator == "in" and "true" in constraint.values and "false" in constraint.values:
            return ConstraintEnum.VALUE_IN_FALSE_AND_TRUE

        if constraint.attribute in ["evseId" , "evse.Id", "startSchedule"]:
            return ConstraintEnum.UNKNOWN_ATTRIBUTE

        if constraint.attribute == "maxLength" and constraint.operator == "equal":
            if constraint.values[0] == "maxLimit":
                return ConstraintEnum.MAX_LENGTH_EQUAL_MAX_LIMIT
            return ConstraintEnum.MAX_LENGTH

        if constraint.attribute == "bytes" and (constraint.operator == "either" or constraint.operator == "equal"):
            return ConstraintEnum.BYTES_FIX

        if (constraint.attribute == "value" or constraint.attribute == "values") and constraint.operator == "in":
            return ConstraintEnum.ENUM

        if constraint.attribute == "type" and constraint.operator == "equal":
            if "custom" in constraint.values:
                return ConstraintEnum.UNTESTABLE_CONSTRAINT
            return ConstraintEnum.TYPE_EQUAL

        if constraint.attribute == "required" and constraint.operator == "equal" and constraint.values[0] == "false":
            return ConstraintEnum.REQUIRED_EQUAL_FALSE

        if constraint.attribute == "required" and constraint.operator == "equal" and "true" in constraint.values:
            return ConstraintEnum.REQUIRED_EQUAL_TRUE

        if constraint.attribute == "optional" and constraint.operator == "equal" and "true" in constraint.values:
            return ConstraintEnum.OPTIONAL_EQUAL_TRUE

        if constraint.values and str(constraint.values[0]).startswith("agreed"):
            return ConstraintEnum.AGREED_UPON_BY_ALL_PARTIES

        if constraint.attribute == "case" and constraint.values[0] == "insensitive":
            return ConstraintEnum.CASE_INSENSITIVE

        if constraint.attribute == "case" and constraint.values[0] == "sensitive":
            return ConstraintEnum.CASE_SENSITIVE

        if constraint.values and constraint.values[0] == "hexadecimal":
            return ConstraintEnum.FORMAT_EQUAL_HEX

        if constraint.attribute == "javaType" and constraint.operator == "equal":
            return ConstraintEnum.JAVA_TYPE_EQUAL

        if constraint.attribute in ["format","encoding"] and constraint.operator == "equal" and ("utf8" in constraint.values or "UTF-8" in constraint.values):
            return ConstraintEnum.FORMAT_EQUAL_UTF8

        if constraint.attribute == "format" and constraint.operator == "equal":
            if constraint.values[0].lower() == "utf8":
                return ConstraintEnum.FORMAT_EQUAL_UTF8
            if constraint.values[0].lower() in ["human-readable", "human readable"]:
                return ConstraintEnum.FORMAT_EQUAL_HUMAN_READABLE
            return ConstraintEnum.FORMAT_EQUAL

        if constraint.attribute in ["value", "values"] and constraint.operator == "equal":
            if "" in constraint.values:
                return ConstraintEnum.VALUE_EQUAL_EMPTY_STRING
            else:
                return ConstraintEnum.VALUE_EQUAL

        if constraint.attribute == "minItems" and constraint.operator in ["equal", "ge"]:
            return ConstraintEnum.MIN_ITEMS_EQUAL

        if constraint.attribute == "maxItems" and (constraint.operator == "equal" or constraint.operator == "max"):
            if "maxScheduleTuples" in constraint.values:
                return ConstraintEnum.MAX_ITEMS_EQUAL_MAX_SCHEDULE_TUPLES
            return ConstraintEnum.MAX_ITEMS_EQUAL

        if constraint.attribute == "encoding" and constraint.operator == "equal":
            return ConstraintEnum.ENCODING_EQUAL

        if constraint.attribute == "prefix" and constraint.operator == "notEqual":
            return ConstraintEnum.PREFIX_NOT_EQUAL

        if constraint.attribute == "leadingZeros" and constraint.operator == "equal" and "false" in constraint.values:
            return ConstraintEnum.NOT_LEADING_ZEROS

        if constraint.attribute == "implemented" and constraint.operator == "equal" and "false" in constraint.values:
            return ConstraintEnum.IMPLEMENTED_EQUAL_FALSE

        if constraint.attribute == "value" and constraint.operator == "from":
            if constraint.values[0] == "Appendix.StandardizedUnitsOfMeasure.Values":
                return ConstraintEnum.VALUE_FROM_MEASUREMENTS_APPENDICES
            if ("Appendix.StandardizedComponents.Names" in constraint.values[0] 
                    or "standardized component names" in constraint.values[0]):
                return ConstraintEnum.VALUE_FROM_STANDARDIZED_COMPONENT_NAMES
            if "Appendix.StandardizedVariables.Names" in constraint.values[0]:
                return ConstraintEnum.VALUE_FROM_STANDARDIZED_VARIABLE_NAMES
            if "Appendix.SecurityEvents.Names" in constraint.values[0]:
                return ConstraintEnum.VALUE_FROM_SECURITY_EVENTS_LIST
            if "Appendix.DisplayMessageCtrlr.SupportedPriorities" in constraint.values[0]:
                return ConstraintEnum.VALUE_FROM_UNDEFINED

            return ConstraintEnum.VALUE_FROM

        if constraint.attribute in ["value", "values"] and constraint.operator == "notEqual":
            return ConstraintEnum.VALUE_NOT_EQUAL

        if constraint.attribute in ["value", "values"] and constraint.operator == "gt":
            return ConstraintEnum.VALUE_GT

        if constraint.attribute in ["value", "values"] and constraint.operator == "ge":
            return ConstraintEnum.VALUE_GE

        if constraint.attribute == "minLength"and constraint.operator == "equal":
            return ConstraintEnum.VALUE_GE

        if constraint.attribute == "status" and constraint.operator == "equal":
            return ConstraintEnum.STATUS_EQUAL

        if constraint.attribute == "wasProvidedIn" and constraint.operator in ["equal", "or"]:
            return ConstraintEnum.WAS_PROVIDED_IN

        if constraint.attribute == "specification" and constraint.operator == "in" and "ISO 15118 schema versions" in constraint.values:
            return ConstraintEnum.SPEC_IN_ISO15118

        if constraint.attribute == "specification" and constraint.operator == "in" and "RFC5646" in constraint.values:
            return ConstraintEnum.SPEC_IN_RFC5646

        if constraint.attribute == "default" and constraint.operator == "equal":
            return ConstraintEnum.DEFAULT_EQUAL

        if constraint.attribute == "decimalPlaces" and constraint.operator == "max":
            return ConstraintEnum.DECIMAL_PLACES_MAX

        if constraint.attribute == "characterSet" and constraint.operator == "equal" and "UTF-8" in constraint.values:
            return ConstraintEnum.CHARACTER_SET_UTF8

        if constraint.attribute == "characterSet" and constraint.operator == "in":
            return ConstraintEnum.CHARACTER_SET_IN

        if constraint.attribute == "bit" and constraint.operator == "equal":
            return ConstraintEnum.BIT_EQUAL

        if constraint.attribute == "removeField" and constraint.operator == "equal" and "true" in constraint.values:
            return ConstraintEnum.REMOVE_FIELD_EQUAL_TRUE

        if constraint.attribute in ["value", "values"] and constraint.operator == "between":
            return ConstraintEnum.VALUE_BETWEEN

        if constraint.attribute == "representation" and constraint.operator == "equal":
            return ConstraintEnum.REPRESENTATION_EQUAL

        if constraint.attribute == "implemented" and constraint.operator == "equal" and "true" in constraint.values:
            return ConstraintEnum.IMPLEMENTED_EQUAL_TRUE

        if constraint.attribute == "implemented" and constraint.operator == "equal" and "custom" in constraint.values:
            return ConstraintEnum.IMPLEMENTED_EQUAL_CUSTOM

        if constraint.attribute == "maximum" and constraint.operator == "equal":
            return ConstraintEnum.MAXIMUM_EQUAL

        if constraint.attribute == "configuration"  and constraint.operator == "equal":
            return ConstraintEnum.CONFIGURATION_EQUAL

        if "transactionDuration" in constraint.values or "TransactionDuration" in constraint.values or "duration of the transaction" in constraint.values or "timeSpentCharging <= transactionDuration" in constraint.values:
            return ConstraintEnum.VALUE_MAX_DURATION_OF_THE_TRANSACTION

        if constraint.attribute == "contentConfiguredBy" and constraint.operator in ["equal", "in"]:
            return ConstraintEnum.CONTENT_CONFIGURED_BY

        if constraint.attribute == "sendingDependsOn" and constraint.operator == "equal":
            return ConstraintEnum.SENDING_DEPENDS_ON_EQUAL

        if constraint.attribute == "wasStoredIn" and constraint.operator == "equal" and "CSMS" in constraint.values:
            return ConstraintEnum.WAS_STORED_IN_CSMS

        if constraint.attribute == "canVerification" and constraint.operator == "equal":
            return ConstraintEnum.CAN_VERIFICATION_EQUAL

        if constraint.attribute == "signedWith" and constraint.operator == "and":
            return ConstraintEnum.SIGNED_WITH_AND

        if constraint.attribute == "oncePerTransaction" and constraint.operator == "equal" and "true" in constraint.values:
            return ConstraintEnum.ONCE_PER_TRANSACTION_EQUAL_TRUE
        if constraint.attribute == "variable" and constraint.operator == "equal":
            if "variable.OCPPCommCtrlr.HeartbeatInterval" in constraint.values:
                return ConstraintEnum.VARIABLE_EQUAL_HEART_BEAT_INTERVAL

        if constraint.attribute == "minimum" and constraint.operator == "equal":
            if 'true' in constraint.values:
                return ConstraintEnum.MINIMUM_EQUAL_TRUE

        if constraint.attribute == "ChargingProfilePurpose" and constraint.operator == "equal":
            return ConstraintEnum.CHARGING_PROFILE_PURPOSE_EQUAL

        if constraint.attribute == "relevant" and constraint.operator == "equal":
            return ConstraintEnum.RELEVANT_EQUAL
        if constraint.attribute == "certificateType" and constraint.operator == "equal":
            return ConstraintEnum.CERTIFICATE_TYPE_EQUAL

        if constraint.attribute == "unit":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if any("wait time" in str(value) or "heartbeat interval" in str(value) for value in constraint.values):
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if constraint.attribute == "currency" and constraint.operator == "equal":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if constraint.attribute == "required" and constraint.operator == "either":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if constraint.attribute == "messageType" and constraint.operator == "equal" and "error" in constraint.values:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if any("last certificate of its type" in str(value) or "last one from its certificate" in str(value) for value in constraint.values):
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if "monitorValue" in constraint.values:
            return ConstraintEnum.VALUE_MONITOR_VALUE

        if "certificateTypeIncludedInSignCertificateRequest" == constraint.attribute:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if constraint.attribute == "triggeredBy" and constraint.operator == "equal" and "TriggerMessageRequest" in constraint.values:
            return ConstraintEnum.UNTESTABLE_CONSTRAINT

        if constraint.attribute == "provided" and constraint.operator == "equal":
            return ConstraintEnum.UNTESTABLE_CONSTRAINT
        return None