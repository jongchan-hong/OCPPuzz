from parser_modules.json.json_schema import get_json_schemas
from constants.version_config import version201
from parser_modules.parser import Parser
from storage.entity.scenario_collect_detail_entity import ScenarioCollectDetailEntity
from storage.loader.model_loader import ModelLoader
import os
from storage.entity.base_entity import session
from scenario_collector_modules.scenario_set import ScenarioSet
loader = ModelLoader("storage.entity")
loader.load_models()

scenario_collect_id_list = list(range(153, 156))
config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)
dataset_dir = os.path.join(os.getcwd(), "dataset")
os.makedirs(dataset_dir, exist_ok=True)

output_path = os.path.join(dataset_dir, "scenario_result.json")

scenario_collect_detail_list: list[ScenarioCollectDetailEntity] = session.query(
    ScenarioCollectDetailEntity).filter(
    ScenarioCollectDetailEntity.scenario_collect_id.in_(scenario_collect_id_list),
    ScenarioCollectDetailEntity.reference_value == None
).all()

scenario_set = ScenarioSet(parser=parser, json_schemas=json_schemas)
for scenario_collect_detail in scenario_collect_detail_list:
    scenario_set.add(scenario_collect_detail.to_dto())

with open(output_path, "w", encoding="utf-8") as f:
    f.write("[\n" + ",\n".join(item.to_json() for item in scenario_set) + "\n]")