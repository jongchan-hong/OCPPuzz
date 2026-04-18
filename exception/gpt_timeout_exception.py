from exception.gpt_exception_interface import GPTExceptionInterface


class GPTTimeOutException(GPTExceptionInterface, Exception):
    def __init__(self, timeout: int):
        super().__init__(f"Timeout occurred after {timeout} seconds")
        self.timeout = timeout

    def get_instruction_message_for_gpt(self) -> str:
        return f"# Timeout : {self.timeout}"