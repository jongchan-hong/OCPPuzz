class GPTExceptionInterface(Exception):
    def get_instruction_message_for_gpt(self) -> str:
        return "Exception occurred, additional instructions needed."