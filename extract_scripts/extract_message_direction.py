import os

from parser_modules.json.json_schema import get_json_schemas
from constants.version_config import version201, Config
from parser_modules.parser import Parser
from storage.entity.base_entity import Base, session
from storage.entity.message_direction_entity import MessageDirectionEntity
from storage.db_engine import engine
import json
from storage.loader.model_loader import ModelLoader

loader = ModelLoader("storage.entity")
loader.load_models()
Base.metadata.create_all(engine)
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)


message_direction_entity = session.query(MessageDirectionEntity).filter_by(file_path=config.document_path).first()

result = message_direction_entity.get_scenario_collect_instructions()
dataset_dir = os.path.join(os.getcwd(), "dataset")
os.makedirs(dataset_dir, exist_ok=True)
output_path = os.path.join(dataset_dir, "message_direction_result.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Extract Success: {output_path}")