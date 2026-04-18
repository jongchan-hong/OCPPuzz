from llm_modules.instruction_configs.message_direction_instruction_config import GPTExceptionInterface

class MessageDirectionValidateException(GPTExceptionInterface, Exception):
    def __init__(self, content: str):
        super().__init__(f"content")
        self.content = content

    def get_instruction_message_for_gpt(self) -> str:
        print(self.content)
        return f"# validation error : {self.content}"