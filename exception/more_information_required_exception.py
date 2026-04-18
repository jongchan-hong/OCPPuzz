
from llm_modules.instruction_configs.message_direction_instruction_config import GPTExceptionInterface

class MoreInformationRequiredException(GPTExceptionInterface, Exception):
    def __init__(self, message: str, description:str):
        super().__init__(f"MoreInformationRequiredException")
        self.message = message
        self.description = description

    def get_instruction_message_for_gpt(self) -> str:
        return f"# {self.message} description: {self.description}"