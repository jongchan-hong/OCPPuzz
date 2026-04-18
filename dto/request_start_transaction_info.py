from dataclasses import dataclass
@dataclass
class RequestStartTransactionInfo:
    remote_start_id: int
    id_token: str
    token_type: str