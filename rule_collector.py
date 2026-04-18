import os

from dotenv import load_dotenv

from parser_modules.parser import Parser
from parser_modules.json.json_schema import get_json_schemas, get_description_and_properties_from_schemas

from constants.fail_cause import get_fail_cause
from constants.version_config import version201, Config
from dto.constraint_collect_dto import RuleExtractionResult, AdditionalPageRequest
from storage.entity.base_entity import Base, session
from storage.entity.rule_collect_detail_entity import RuleCollectDetailEntity
from storage.entity.rule_collect_entity import RuleCollectEntity
from storage.entity.rule_collect_fail_entity import RuleCollectFailEntity
from storage.entity.gpt_rule_collect_log_entity import GPTRuleCollectLogEntity
from llm_modules.instruction_configs.constraint_instruction_config import ConstraintInstructionConfig
from storage.db_engine import engine
from typing import List, Optional
from dto.gpt_retry_dto import GPTRetryDTO
import json
import logging
from llm_modules.gpt import GPTModule
import queue
import time
from parser_modules.s3_upload_config_dto import S3UploadConfigDTO
import re
from storage.loader.model_loader import ModelLoader
from storage.s3 import get_s3_config

Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)
COLLECT_CNT = 1
loader = ModelLoader("storage.entity")
loader.load_models()

load_dotenv()
API_KEY = input("Write your GPT API Key >> ")
if not API_KEY:
    print("API Key is missing")
    exit()
RETRY_MAX_CNT = 10

s3_config = get_s3_config()

if not API_KEY:
    print("Need API_KEY .env")
    exit()

def register(
        rule_collect_entity:RuleCollectEntity,
        content,
        name:str,
        retry_dto: Optional[GPTRetryDTO] = None,
        additional_page_request_list: Optional[ List[AdditionalPageRequest]] = None
):
    if retry_dto is not None and retry_dto.retry >= RETRY_MAX_CNT:
        register_fail_cause(rule_collect_entity, name, retry_dto)
        return

    time.sleep(5)
    constraint_instruction_config = ConstraintInstructionConfig(
        content=content,
        parser=parser,
        gpt_retry_dto=retry_dto,
        additional_page_request_list= additional_page_request_list,
        s3_config=s3_config
    )
    constraint_instruction_config.append_previous_responses(name, rule_collect_entity)
    gpt_module = GPTModule(API_KEY)
    result: str = ""
    rule_extraction_result:Optional[RuleExtractionResult] = None
    currentException:Optional[Exception] = None
    is_clear = False


    try:
        result = gpt_module.run(constraint_instruction_config)

        if result != constraint_instruction_config.end_mark:
            result_dict = json.loads(result)
            print(json.dumps(result_dict, ensure_ascii=False))
            rule_extraction_result = RuleExtractionResult(**result_dict)
        else:
            is_clear = True

    except Exception as e:
        logging.exception("logging exception:")
        print(e)
        currentException = e
        match = re.search(r"Please try again in ([\d.]+)s", str(e))
        if match:
            delay = float(match.group(1))
            print(f"Rate limit hit. Sleeping for {delay} seconds...")
            time.sleep(delay)
    finally:
        session.add(
            GPTRuleCollectLogEntity(
                rule_collect_entity=rule_collect_entity,
                object_name=name,
                model=constraint_instruction_config.model,
                timeout=constraint_instruction_config.timeout,
                temperature=constraint_instruction_config.temperature,
                response=result,
                messages=constraint_instruction_config.messages,
            )
        )

        if rule_extraction_result:
            if rule_extraction_result.rules:
                for constraint_collect_dto in rule_extraction_result.rules:
                    session.add(
                        RuleCollectDetailEntity(
                            rule_collect_entity=rule_collect_entity,
                            object_name=name,
                            constraint_collect_dto=constraint_collect_dto
                        )
                    )
        try:
            session.flush()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        session.commit()
        if not is_clear:

            combined_additional_pages = (additional_page_request_list or []) + (rule_extraction_result.additional_page_request_list if rule_extraction_result and rule_extraction_result.additional_page_request_list else [])
            if retry_dto:
                retry_dto.retry = retry_dto.retry + 1
            else:
                retry_dto = GPTRetryDTO(
                    retry=1,
                    error_content=result,
                    exception=currentException
                )
            register(
                rule_collect_entity = rule_collect_entity,
                content=content,
                name=name,
                retry_dto=retry_dto,
                additional_page_request_list= combined_additional_pages
            )





def register_fail_cause(rule_collect_entity, name, retry_dto):
    fail_cause = get_fail_cause(retry_dto)
    session.add(
        RuleCollectFailEntity(
            rule_collect_entity=rule_collect_entity,
            message=name,
            fail_cause=fail_cause
        )
    )

def enqueue_data_type(type_name):
    if type_name not in processed_data_types:
        data_type_queue.put(type_name)
        processed_data_types.add(type_name)

rule_collect_entity = session.query(RuleCollectEntity).filter(
        RuleCollectEntity.id.in_([166])
    ).first()
is_run = False

for message in parser.messages:
    if message.name == "SetVariableMonitoringRequest":
        is_run = True
    if is_run:
        description, properties = get_description_and_properties_from_schemas(message, json_schemas)
        content = message.get_information(parser, description, properties)
        register(rule_collect_entity, content, message.name)
for data_type in parser.data_types:
    description, properties = get_description_and_properties_from_schemas(data_type, json_schemas)
    content = data_type.get_information(parser, description, properties)
    register(rule_collect_entity, content, data_type.name)

repeat_cnt = 9

for i in range(repeat_cnt):
    rule_collect_entity = RuleCollectEntity(config.document_path)
    session.add(rule_collect_entity)
    session.commit()
    data_type_queue = queue.Queue()
    processed_data_types = set()

    if parser.primitive_data_types:
        name = "PrimitiveDatatypes"
        content = {}
        content['object_name'] = name
        content["fields"] = []
        for primitive_data_type in parser.primitive_data_types:
            content["fields"].append(primitive_data_type.get_information())
        register(rule_collect_entity, json.dumps(content), name)

    for message in parser.messages:
        description, properties = get_description_and_properties_from_schemas(message, json_schemas)
        content = message.get_information(parser, description, properties)
        register(rule_collect_entity, content, message.name)
    for data_type in parser.data_types:
        description, properties = get_description_and_properties_from_schemas(data_type, json_schemas)
        content = data_type.get_information(parser, description, properties)
        register(rule_collect_entity, content, data_type.name)
