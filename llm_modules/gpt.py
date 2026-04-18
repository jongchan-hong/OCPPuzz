from openai import OpenAI

from llm_modules.instruction_configs.instruction_config import InstructionConfig
from llm_modules.llm import LLM


class GPTModule(LLM):
    def __init__(self, token: str):
        self.client = OpenAI(api_key=token)

    def run(self, instruction_config:InstructionConfig):
        response = self.client.chat.completions.create(
            model= instruction_config.model,
            messages= instruction_config.getMessages(),
            timeout = instruction_config.timeout,
            temperature=instruction_config.temperature
        )
        return response.choices[0].message.content
