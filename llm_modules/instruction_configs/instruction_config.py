from typing import List, Optional
from dto.gpt_retry_dto import GPTRetryDTO
from dto.instruction_message_dto import InstructionMessageDTO
from exception.gpt_exception_interface import GPTExceptionInterface

class InstructionConfig:
    content: str
    temperature: float
    gpt_retry_dto: Optional[GPTRetryDTO]
    model: str
    system_instructions: str
    run_request_instructions: List[str]
    timeout: int
    messages: List[InstructionMessageDTO]
    def getMessages(self) -> List[dict]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    @property
    def run_request_instructions(self) -> List[str]:
        instructions = self._run_request_instructions.copy()
        if self.gpt_retry_dto:
            instructions.append(
                f"# This question is a retry, and the response you previously provided is as follows: {self.gpt_retry_dto.error_content}"
            )
            if isinstance(self.gpt_retry_dto.exception, GPTExceptionInterface):
                instructions.append(self.gpt_retry_dto.exception.get_instruction_message_for_gpt())
            else:
                instructions.append(f"# Internal Error Occurred: {str(self.gpt_retry_dto.exception)}")
        return instructions

    @run_request_instructions.setter
    def run_request_instructions(self, value: List[str]):
        self._run_request_instructions = value