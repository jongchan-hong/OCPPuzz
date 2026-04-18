from llm_modules.instruction_configs.message_direction_instruction_config import GPTExceptionInterface

class NotSupportedReferenceMessageException(GPTExceptionInterface, Exception):
    def __init__(self, message: str):
        super().__init__(f"NotSupportedReferenceMessageException")
        self.message = message

    def get_instruction_message_for_gpt(self) -> str:
        return f"# {self.message} is Not supported"