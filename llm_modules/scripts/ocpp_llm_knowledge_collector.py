from storage.entity.llm_knowledge_collect_detail_entity import LLMKnowledgeCollectDetailEntity
from storage.entity.llm_knowledge_collect_entity import LLMKnowledgeCollectEntity
from storage.entity.llm_knowledge_collect_fail_entity import LLMKnowledgeCollectFailEntity
from storage.entity.llm_knowledge_collect_log_entity import LLMKnowledgeCollectLogEntity
from llm_modules.instruction_configs.knowledge_instruction_config import KnowledgeInstructionConfig
from parser_modules.parser import Parser
from constants.fail_cause import get_fail_cause
from constants.version_config import version201, Config

from typing import Optional
from dto.gpt_retry_dto import GPTRetryDTO
from parser_modules.json.json_schema import get_json_schemas
import traceback

import json
from llm_modules.gpt import GPTModule
from dotenv import load_dotenv
from storage.entity.base_entity import Base, session
from storage.db_engine import engine
from llm_modules.llm import LLM
from llm_modules.ollama_module import OllamaModule
import os
load_dotenv()
API_KEY = os.environ.get('API_KEY')
Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)

objects = parser.messages + parser.data_types
llm_knowledge_collect_entity = LLMKnowledgeCollectEntity(config.document_path)
session.add(llm_knowledge_collect_entity)
session.commit()

llm_provider_models = {
    "openai": {
        "model": [
            "gpt-4o"
        ]
    },
    "ollama": {
        "model": [
            "gemma3:27b",
            "llama3",
            "llama4"
        ]
    }
}
RETRY_MAX_CNT = 10

# content=f"Please provide the field definitions for the object `{object_data.name}` itself.",
def register(
        llm_knowledge_collect_entity:LLMKnowledgeCollectEntity,
        object_name:str,
        provider:str,
        model:str,
        retry_dto: Optional[GPTRetryDTO] = None
):
    if retry_dto is not None and retry_dto.retry >= RETRY_MAX_CNT:
        register_fail_cause(
            llm_knowledge_collect_entity = llm_knowledge_collect_entity,
            provider = provider,
            object_name = object_name,
            retry_dto = retry_dto,
            model=model
        )
        return

    instruction_config = KnowledgeInstructionConfig (
        content= f"Please provide the field definitions for the object `{object_name}` itself.",
        model = model,
        retry_dto = retry_dto
    )
    module:Optional[LLM] = None
    is_clear = False
    response: str = ""
    currentException: Optional[Exception] = None
    match provider:
        case "openai":
            module = GPTModule(API_KEY)
        case "ollama":
            module = OllamaModule()
    try:
        response = module.run(instruction_config)
        receive_field_info_list = json.loads(response)
        print("aa response:", response)

        llm_knowledge_collect_detail_entity = LLMKnowledgeCollectDetailEntity(
            llm_knowledge_collect_entity = llm_knowledge_collect_entity,
            provider = provider,
            model = model,
            object_name = object_name,
            response = response
        )
        session.add(llm_knowledge_collect_detail_entity)
        is_clear = True
    except Exception as e:
        is_clear = False
        currentException = e
        print("[Exception]")
        traceback.print_exc()
    finally:
        session.add(
            LLMKnowledgeCollectLogEntity(
                llm_knowledge_collect_entity = llm_knowledge_collect_entity,
                object_name = object_name,
                provider = provider,
                model = instruction_config.model,
                knowledge_instruction_config = instruction_config,
                response=response
            )
        )
        session.commit()
        if not is_clear:
            if retry_dto:
                retry_dto.retry = retry_dto.retry + 1
            else:
                retry_dto = GPTRetryDTO(
                    retry=1,
                    error_content=response,
                    exception=currentException
                )
            register(
                llm_knowledge_collect_entity=llm_knowledge_collect_entity,
                object_name=object_data.name,
                provider=provider,
                model=model,
                retry_dto=retry_dto,
            )

def register_fail_cause(llm_knowledge_collect_entity, provider, model, object_name, retry_dto):
    fail_cause = get_fail_cause(retry_dto)
    session.add(
        LLMKnowledgeCollectFailEntity(
            llm_knowledge_collect_entity=llm_knowledge_collect_entity,
            object_name=object_name,
            fail_cause=fail_cause,
            provider = provider,
            model = model
        )
    )
    session.commit()

for object_data in objects:
    for provider, config in llm_provider_models.items():
        for model in config["model"]:
            register(
                llm_knowledge_collect_entity = llm_knowledge_collect_entity,
                object_name= object_data.name,
                provider = provider,
                model = model
            )