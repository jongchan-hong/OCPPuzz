from typing import Optional
from dto.gpt_retry_dto import GPTRetryDTO
from dto.instruction_message_dto import InstructionMessageDTO
from llm_modules.instruction_configs.instruction_config import InstructionConfig
from exception.gpt_exception_interface import GPTExceptionInterface
import textwrap

class KnowledgeInstructionConfig(InstructionConfig):

    def __init__(self, content: str, model, retry_dto: Optional[GPTRetryDTO] = None):
        self.content = content
        self.temperature = 0.0
        self.model = model
        self.retry_dto = retry_dto
        self.timeout = 120

        self.system_main_instruction = InstructionMessageDTO(
            role="system", content=textwrap.dedent('''
            You are being evaluated on your understanding of the OCPP 2.0.1 protocol.
        
            Given the name of an OCPP 2.0.1 message object, return a structured list of its fields in JSON format. For each field, include the following information:
            
            - `name`: the field name as used in the protocol
            - `type`: the data type (e.g., string, integer, boolean, TestType, identifierString, string[0..5600], etc.)
            - `card`: the cardinality ("1..1" if required, "0..1" if optional, or "1..n", "0..n", "0..*" for arrays)
            
            Do not return any other explanation or commentary. Only return the result as a JSON array. Do not include ``` or any other markdown formatting.
            ''')
        )
        self.assistant_expected_output_instruction = InstructionMessageDTO(
            role="assistant",
            content=textwrap.dedent('''
                Expected output:
                [
                  {
                    "name": "chargingStation",
                    "type": "ChargingStation",
                    "card": "0..1"
                  },
                  {
                    "name": "reason",
                    "type": "TestType",
                    "card": "1..1"
                  },
                  {
                    "name": "meterValue",
                    "type": "MeterValueType",
                    "card": "0..*"
                  }
                ]
            ''')
        )

        self.messages = [
            self.system_main_instruction,
            self.assistant_expected_output_instruction,
            InstructionMessageDTO(role="user", content=self.content)
        ]

        if self.retry_dto:
            retry_content = f"# This question is a retry, and the response you previously provided is as follows: {self.retry_dto.error_content}"
            if isinstance(self.retry_dto.exception, GPTExceptionInterface):
                retry_content += "\n " + self.retry_dto.exception.get_instruction_message_for_gpt()
            else:
                retry_content += "\n " + f"# Internal Error Occurred: {str(self.retry_dto.exception)}"
            self.messages.append(InstructionMessageDTO(role="assistant", content=retry_content))