from typing import Optional
from dto.gpt_retry_dto import GPTRetryDTO
from dto.instruction_message_dto import InstructionMessageDTO
from llm_modules.instruction_configs.instruction_config import InstructionConfig
from exception.gpt_exception_interface import GPTExceptionInterface

class MessageDirectionInstructionConfig(InstructionConfig):
    IMPOSSIBLE = "[IMPOSSIBLE]"

    def __init__(self, content: str, gpt_retry_dto: Optional[GPTRetryDTO] = None):
        self.content = content
        self.temperature = 0
        self.gpt_retry_dto = gpt_retry_dto
        self.model = "gpt-4o"
        self.timeout = 60
        self.system_instructions = (
            "Analyze OCPP message descriptions and determine the ’from’ and ’to’ fields in JSON format. The ’from’ field " +
            "represents the sender of the message, and the ’to’ field represents the receiver. Possible values for both ’from’ and ’to’ " +
            "are ’Charging Station’ and ’CSMS’."
        )

        self.rule_instructions = [
            "Rules:",
            "1. Both 'from' and 'to' should be arrays because there may be multiple sources or destinations.",
            "2. If the 'from' and 'to' can be determined with certainty, return them as arrays containing the respective values.",
            "3. If you need the description of a referenced message, fill in the additional_info_required field as shown in the example.",
            "4. If it is impossible to determine 'from' and 'to', set the value to '[\"[IMPOSSIBLE]\"]'.",
        ]
        self.examples = [
            "# Example",
            "## Case 1: Determined with certainty",
            'Input:\n{ "description": "Used by the CSMS to request an overview of the installed certificates on a Charging Station." }',
            'Output:\n{ "from": ["CSMS"], "to": ["Charging Station"], "additional_info_required": null }',
            "## Case 2: Additional information required",
            'Input:\n{ "description": "Response to a GetInstalledCertificateIDsRequest" }',
            'Output:\n{ "from": [], "to": [], "additional_info_required": { "reference_message": "GetInstalledCertificateIDsRequest" } }',
            "## Case 3: Impossible to determine",
            'Input:\n{ "description": "" }',
            'Output:\n{ "from": ["[IMPOSSIBLE]"], "to": ["[IMPOSSIBLE]"], "additional_info_required": null }',
        ]

        self.messages = [
            InstructionMessageDTO(role="system", content=self.system_instructions),
            InstructionMessageDTO(role="developer", content="\n".join(self.rule_instructions)),
            InstructionMessageDTO(role="assistant", content="\n".join(self.examples)),
            InstructionMessageDTO(role="user", content=self.content)
        ]

        if self.gpt_retry_dto:
            append_content = []
            append_content.append(
                f"# This question is a retry, and the response you previously provided is as follows: {self.gpt_retry_dto.error_content}"
            )
            if isinstance(self.gpt_retry_dto.exception, GPTExceptionInterface):
                append_content.append(self.gpt_retry_dto.exception.get_instruction_message_for_gpt())
            else:
                append_content.append(f"# Internal Error Occurred: {str(self.gpt_retry_dto.exception)}")
            self.messages.append(InstructionMessageDTO(role="developer", content="\n".join(append_content)))