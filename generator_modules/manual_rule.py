from typing import List

from dto.constraint_collect_dto import Condition, Constraint, Rule, Cause
from constants.ocpp_version import OcppVersion
from util.signature.signature import CITRINE_ENCODING_METHOD


class ManualRule:
    object_name:str
    field_name:str
    rule:Rule

    def __init__(self, object_name:str, field_name:str, rule:Rule):
        self.object_name = object_name
        self.field_name = field_name
        self.rule = rule

manual_cause = Cause(
    name = "manual",
    sentence=""
)

TRANSACTION_ID_MUST_EXIST_IF_NOT_STARTED = ManualRule(
    object_name="TransactionEventRequest",
    field_name="eventType",
    rule=Rule(
        causes= [manual_cause],
        conditions=[
            Condition(
                target="fixValueContainer.transactionInfo.transactionId",
                attribute="exist",
                operator="equal",
                values=[
                    "false"
                ]
            )
        ],
        constraint=Constraint(
            attribute="value",
            operator="equal",
            values=["Started"]
        )
    )
)

PUBLIC_KEY_CAN_VERIFICATION_SIGNED_METER_DATA = ManualRule(
    object_name="SignedMeterValueType",
    field_name="publicKey",
    rule=Rule(
        causes= [manual_cause],
        conditions=[],
        constraint=Constraint(
            attribute="canVerification",
            operator="equal",
            values=["field.signedMeterData"]
        )
    )
)

CITRINE_SUPPORTED_ENCODING_METHOD = ManualRule(
    object_name="SignedMeterValueType",
    field_name="encodingMethod",
    rule=Rule(
        causes= [manual_cause],
        conditions=[],
        constraint=Constraint(
            attribute="value",
            operator="in",
            values=CITRINE_ENCODING_METHOD
        )
    )
)

CITRINE_SUPPORTED_SIGNING_METHOD = ManualRule(
    object_name="SignedMeterValueType",
    field_name="signingMethod",
    rule=Rule(
        causes= [manual_cause],
        conditions=[],
        constraint=Constraint(
            attribute="value",
            operator="in",
            values=["RSASSA-PKCS1-v1_5"]
        )
    )
)

CUSTOMER_INFORMATION_REQUEST_ID_WAS_PROVIDED_IN = ManualRule(
    object_name="NotifyCustomerInformationRequest",
    field_name="requestId",
    rule=Rule(
        causes= [manual_cause],
        conditions=[],
        constraint=Constraint(
            attribute="wasProvidedIn",
            operator="equal",
            values=["CustomerInformationRequest"]
        )
    )
)

THE_FIRST_TRANSACTION_EVENT_TYPE_IS_STARTED = ManualRule(
    object_name="TransactionEventRequest",
    field_name="eventType",
    rule=Rule(
        causes= [manual_cause],
        conditions=[
            Condition(
                target="context.isFirstTransaction",
                attribute="values",
                operator="equal",
                values=[
                    "true"
                ]
            )
        ],
        constraint=Constraint(
            attribute="value",
            operator="equal",
            values=["Started"]
        )
    )
)


OCPP_201_MANUAL_RULE_LIST = [
    CUSTOMER_INFORMATION_REQUEST_ID_WAS_PROVIDED_IN,
    THE_FIRST_TRANSACTION_EVENT_TYPE_IS_STARTED
]

def get_manual_rule_list(version:OcppVersion)->List[ManualRule]:
    match version:
        case OcppVersion.version_201:
            return OCPP_201_MANUAL_RULE_LIST

def get_id_token_manual_rule(id_token_dict)->ManualRule:
    return ManualRule(
        object_name="TransactionEventRequest",
        field_name="idToken",
        rule=Rule(
            causes=[manual_cause],
            conditions=[],
            constraint=Constraint(
                attribute="values",
                operator="equal",
                values=[id_token_dict]
            )
        )
    )




