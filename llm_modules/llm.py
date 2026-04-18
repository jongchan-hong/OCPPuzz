from abc import ABC, abstractmethod

from llm_modules.instruction_configs.instruction_config import InstructionConfig


class LLM(ABC):

    @abstractmethod
    def run(self, instruction_config:InstructionConfig)-> str:
        pass

