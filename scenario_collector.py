import os
import traceback

from dotenv import load_dotenv

from parser_modules.json.json_schema import get_json_schemas, get_json_schema_text
from constants.fail_cause import get_fail_cause
from constants.version_config import version201, Config
from dataset.scripts.message_direction_result import MessageDirectionResult
from dto.constraint_collect_dto import AdditionalPageRequest
from dto.scenario_collect_dto import ScenarioCollectResult
from dto.scenario_page_dto import ScenarioPageDTO
from parser_modules.parser import Parser
from storage.entity.base_entity import session, Base
from storage.entity.gpt_scenario_collect_log_entity import GPTScenarioCollectLogEntity
from storage.entity.scenario_collect_detail_entity import ScenarioCollectDetailEntity
from storage.entity.scenario_collect_entity import ScenarioCollectEntity
from storage.entity.scenario_collect_fail_entity import ScenarioCollectFailEntity

from llm_modules.instruction_configs.scenario_instruction_config import ScenarioInstructionConfig
from storage.db_engine import engine
from typing import List, Optional
from dto.gpt_retry_dto import GPTRetryDTO
import json
from llm_modules.gpt import GPTModule
from storage.loader.model_loader import ModelLoader
from parser_modules.s3_upload_config_dto import S3UploadConfigDTO
from storage.s3 import get_s3_config

COLLECT_CNT = 1
RETRY_MAX_CNT = 10


API_KEY = input("Write your GPT API Key >> ")
if not API_KEY:
    print("API Key is missing")
    exit()


s3_config = get_s3_config()
loader = ModelLoader("storage.entity")
loader.load_models()
Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)
scenario_pages:List[ScenarioPageDTO] = parser.get_scenario_pages()
scenario_collect_entity = ScenarioCollectEntity(config.document_path)
session.add(scenario_collect_entity)
session.commit()
message_direction_result = MessageDirectionResult()


def register(
        scenario_collect_entity:ScenarioCollectEntity,
        scenario_page_dto:ScenarioPageDTO,
        retry_dto: Optional[GPTRetryDTO] = None,
        additional_info_request: Optional[AdditionalPageRequest] = None,
        total_additional_page_request_list:List[AdditionalPageRequest] = None
):
    if retry_dto is not None and retry_dto.retry >= RETRY_MAX_CNT:
        register_fail_cause(scenario_collect_entity, scenario_page_dto.scenario_name, retry_dto)
        return

    scenario_instruction_config = ScenarioInstructionConfig(
        scenario_page_dto=scenario_page_dto,
        parser=parser,
        gpt_retry_dto=retry_dto,
        json_schemas = json_schemas,
        scenario_collect_instructions=message_direction_result.data,
        s3_config=s3_config
    )
    scenario_instruction_config.append_previous_responses(object_name=scenario_page_dto.scenario_name, scenario_collect_entity=scenario_collect_entity, gpt_retry_dto = retry_dto)
    gpt_module = GPTModule(API_KEY)
    result: str = ""
    scenario_collect_result:Optional[ScenarioCollectResult] = None
    currentException: Optional[Exception] = None
    is_clear = False


    if additional_info_request:
        if additional_info_request.additional_schema_message_list and len(additional_info_request.additional_schema_message_list) > 0:
            json_data_list = []
            for message_name in additional_info_request.additional_schema_message_list:
                json_data_list.append(get_json_schema_text(config.json_schema_folder_path, message_name))
            scenario_instruction_config.set_additional_schemas(json_data_list)

        if additional_info_request.additional_page_request_list:
            additional_page_request_list = additional_info_request.additional_page_request_list
            if total_additional_page_request_list is None:
                total_additional_page_request_list = []
            total_additional_page_request_list.extend(additional_page_request_list)
            scenario_instruction_config.set_additional_page(total_additional_page_request_list)

    try:
        print("Run!")
        result = gpt_module.run(scenario_instruction_config)

        if result == scenario_instruction_config.end_mark:
            is_clear = True
        else:
            result_dict = json.loads(result)
            print(json.dumps(result_dict, ensure_ascii=False))
            scenario_collect_result = ScenarioCollectResult(**result_dict)
            if scenario_collect_result.scenario_collect_list and not scenario_collect_result.additional_info_request:
                is_clear = True
                for scenario_collect in scenario_collect_result.scenario_collect_list:
                    scenario_collect_detail_entity = ScenarioCollectDetailEntity(
                        scenario_collect_entity = scenario_collect_entity,
                        scenario_collect_dto= scenario_collect,
                        name = scenario_page_dto.figure_line,
                        scenario_page_dto= scenario_page_dto
                    )
                    session.add(scenario_collect_detail_entity)
    except Exception as e:
        is_clear = False
        currentException = e
        print("[Exception]")
        traceback.print_exc()
    finally:
        session.add(
            GPTScenarioCollectLogEntity(
                scenario_collect_entity=scenario_collect_entity,
                object_name=scenario_page_dto.figure_line,
                model=scenario_instruction_config.model,
                timeout=scenario_instruction_config.timeout,
                temperature=scenario_instruction_config.temperature,
                response=result,
                messages=scenario_instruction_config.messages,
            )
        )
        session.commit()
    if not is_clear:
        if retry_dto:
            retry_dto.retry = retry_dto.retry + 1
        else:
            retry_dto = GPTRetryDTO(
                retry=1,
                error_content=result,
                exception=currentException
            )
        register(
            scenario_collect_entity = scenario_collect_entity,
            scenario_page_dto = scenario_page_dto,
            retry_dto = retry_dto,
            additional_info_request = scenario_collect_result.additional_info_request if scenario_collect_result and scenario_collect_result.additional_info_request else None,
            total_additional_page_request_list = total_additional_page_request_list
        )

def register_fail_cause(scenario_collect_entity, name, retry_dto):
    fail_cause = get_fail_cause(retry_dto)
    session.add(
        ScenarioCollectFailEntity(
            scenario_collect_entity=scenario_collect_entity,
            name=name,
            fail_cause=fail_cause
        )
    )
    session.commit()

for scenario_page in scenario_pages:
    register(
        scenario_collect_entity = scenario_collect_entity,
        scenario_page_dto= scenario_page,
    )