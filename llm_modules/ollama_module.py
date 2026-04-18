from dto.gpt_run_result_dto import MessageDTO
from llm_modules.instruction_configs.instruction_config import InstructionConfig
from llm_modules.llm import LLM
import requests


class OllamaModule(LLM):
    url = "http://localhost:11434/api/chat"

    def run(self, instruction_config:InstructionConfig):
        model = instruction_config.model
        payload = {
            "model": model,
            "messages": instruction_config.getMessages(),
            "options": {
                "temperature": instruction_config.temperature
            },
            "stream": False
        }
        response = requests.post(self.url, json=payload)
        receive_message: MessageDTO = MessageDTO(**response.json().get("message"))
        return receive_message.content
