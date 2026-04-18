from dotenv import load_dotenv
from constants.fail_cause import FailCause, get_fail_cause
from dto.gpt_retry_dto import GPTRetryDTO
from dto.message_direction_dto import MessageDirectionDTO
from storage.entity.base_entity import session, Base
from storage.entity.message_direction_entity import MessageDirectionEntity
from storage.db_engine import engine
from storage.entity.gpt_message_direction_log_entity import GPTMessageDirectionLogEntity
from storage.entity.message_direction_detail_entity import MessageDirectionDetailEntity
from storage.entity.message_direction_fail_entity import MessageDirectionFailEntity

from exception.gpt_impossible_exception import GPTImpossibleException
from exception.more_information_required_exception import MoreInformationRequiredException
from exception.not_supported_reference_message_exception import NotSupportedReferenceMessageException
from llm_modules.instruction_configs.message_direction_instruction_config import MessageDirectionInstructionConfig
from llm_modules.gpt import GPTModule
from parser_modules.parser import Parser
from constants.version_config import Config, version201
from parser_modules.specification.message import Message
from typing import List, Optional
import json
import logging
import time
from storage.loader.model_loader import ModelLoader

loader = ModelLoader("storage.entity")
loader.load_models()

API_KEY = input("Write your GPT API Key >> ")
if not API_KEY:
    print("API Key is missing")
    exit()
version:Config = version201
parser = Parser(version)
load_dotenv()
RETRY_MAX_CNT = 20
Base.metadata.create_all(engine)

message_direction_entity = MessageDirectionEntity(version.document_path)
session.add(message_direction_entity)
session.commit()


def register(
        message_direction_entity: MessageDirectionEntity,
        current_message: Message,
        messages: List[Message],
        retry_dto: Optional[GPTRetryDTO] = None
 ):

   if retry_dto is not None and retry_dto.retry >= RETRY_MAX_CNT:
       fail_cause = get_fail_cause(retry_dto)
       session.add(MessageDirectionFailEntity(message_direction_entity, current_message.name, fail_cause))
       return

   if not current_message.description:
       session.add(MessageDirectionFailEntity(message_direction_entity, current_message.name, FailCause.IMPOSSILBE))
       return
   message_direction_instruction_config = MessageDirectionInstructionConfig(current_message.description, retry_dto)
   gpt_module = GPTModule(API_KEY)
   result: str = ""
   message_direction_dto: Optional[MessageDirectionDTO] = None

   try:
       result = gpt_module.run(message_direction_instruction_config)
       content_dict = json.loads(result)
       message_direction_dto = MessageDirectionDTO(**content_dict)
       validate(message_direction_dto, messages)
       if message_direction_dto is not None:
           session.add(
               MessageDirectionDetailEntity(
                   message_direction_entity=message_direction_entity,
                   action=current_message.name,
                   from_list=message_direction_dto.from_,
                   to_list=message_direction_dto.to
               )
           )
   except NotSupportedReferenceMessageException as e:
       logging.exception("not supported exception:")
       fail_cause = FailCause.IMPOSSILBE
       session.add(MessageDirectionFailEntity(message_direction_entity, current_message.name, fail_cause))
       return

   except Exception as e:
       logging.exception("logging exception:")
       print(e)
       retry = 0
       if retry_dto:
           retry = retry_dto.retry
       retry = retry + 1
       new_retry_dto = GPTRetryDTO(
           retry=retry,
           error_content= result,
           exception= e
       )
       register(message_direction_entity, current_message, messages, new_retry_dto)
   finally:
       if result:
           session.add(
               GPTMessageDirectionLogEntity(
                   message_direction_entity=message_direction_entity,
                   message=current_message.name,
                   model= message_direction_instruction_config.model,
                   timeout= message_direction_instruction_config.timeout,
                   temperature= message_direction_instruction_config.temperature,
                   response= result,
                   messages= message_direction_instruction_config.messages,
               )
           )

       session.flush()
       session.commit()
       time.sleep(0.5)
def validate(message_direction_dto:MessageDirectionDTO, messages: List[Message]):
    if (MessageDirectionInstructionConfig.IMPOSSIBLE in message_direction_dto.from_
            or MessageDirectionInstructionConfig.IMPOSSIBLE in message_direction_dto.to):
        raise GPTImpossibleException()

    if message_direction_dto.additional_info_required is not None \
            and not message_direction_dto.to and not message_direction_dto.from_:
        if message_direction_dto.additional_info_required.reference_message:
            find_message_name = message_direction_dto.additional_info_required.reference_message
            results = list(filter(lambda message: message.name == find_message_name, messages))
            if len(results) == 0:
                raise NotSupportedReferenceMessageException(find_message_name)
            find_message:Message = results[0]
            raise MoreInformationRequiredException(find_message.name, find_message.description)
    return True

print("total: "+str(len(parser.messages)))
for message in parser.messages:
    register(message_direction_entity, message, parser.messages)
session.flush()
session.commit()