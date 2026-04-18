from enum import Enum

class ErrorCode(Enum):
    FormatViolation = "FormatViolation"
    GenericError = "GenericError"
    InternalError = "InternalError"
    MessageTypeNotSupported = "MessageTypeNotSupported"
    NotImplemented = "NotImplemented"
    NotSupported = "NotSupported"
    OccurrenceConstraintViolation = "OccurrenceConstraintViolation"
    PropertyConstraintViolation = "PropertyConstraintViolation"
    ProtocolError = "ProtocolError"
    RpcFrameworkError = "RpcFrameworkError"
    SecurityError = "SecurityError"
    TypeConstraintViolation = "TypeConstraintViolation"