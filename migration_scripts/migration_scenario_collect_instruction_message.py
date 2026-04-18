from storage.entity.gpt_scenario_collect_log_entity import GPTScenarioCollectLogEntity
from storage.entity.migrate_scenario_collect_instruction_message_entity import MigrateScenarioCollectInstructionMessageEntity
from storage.entity.scenario_collect_entity import ScenarioCollectEntity
from storage.db_engine import engine
from storage.loader.model_loader import ModelLoader
loader = ModelLoader("storage.entity")
loader.load_models()
from storage.entity.base_entity import session, Base

Base.metadata.create_all(engine)

gpt_scenario_collect_log_entity_list = (session.query(GPTScenarioCollectLogEntity).filter(
    ScenarioCollectEntity.id.in_(list(range(153, 156)))
).outerjoin(ScenarioCollectEntity, ScenarioCollectEntity.id == GPTScenarioCollectLogEntity.scenario_collect_id)
        .order_by(GPTScenarioCollectLogEntity.created_at.desc()).all())

for gpt_scenario_collect_log_entity in gpt_scenario_collect_log_entity_list:
    for scenario_collect_instruction_message in gpt_scenario_collect_log_entity.messages:
        session.add(MigrateScenarioCollectInstructionMessageEntity.from_entity(scenario_collect_instruction_message))
        session.flush()
session.commit()