import enum

from dto.gpt_retry_dto import GPTRetryDTO
from exception.gpt_impossible_exception import GPTImpossibleException
class FailCause(enum.Enum):
    RETRY_LIMIT = "R"
    IMPOSSILBE = "I"

def get_fail_cause(retry_dto:GPTRetryDTO):
    if isinstance(retry_dto.exception,GPTImpossibleException):
        return FailCause.IMPOSSILBE
    return FailCause.RETRY_LIMIT