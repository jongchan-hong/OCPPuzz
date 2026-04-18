from llm_modules.instruction_configs.message_direction_instruction_config import GPTExceptionInterface

class GPTImpossibleException(GPTExceptionInterface, Exception):
    def get_instruction_message_for_gpt(self) -> str:
        return "# try again"