

from storage.entity.gpt_rule_collect_log_entity import GPTRuleCollectLogEntity
from storage.entity.migrate_rule_collect_instruction_message_entity import MigrateRuleCollectInstructionMessageEntity
from storage.entity.rule_collect_entity import RuleCollectEntity
from storage.db_engine import engine
from storage.loader.model_loader import ModelLoader

loader = ModelLoader("storage.entity")
loader.load_models()

from storage.entity.base_entity import session, Base

Base.metadata.create_all(engine)

gpt_rule_collect_log_entity_list = (session.query(GPTRuleCollectLogEntity).filter(
    RuleCollectEntity.id.in_([164, 165, 166, 167, 168, 169, 170, 171, 172, 173])
).outerjoin(RuleCollectEntity, RuleCollectEntity.id == GPTRuleCollectLogEntity.rule_collect_id)
        .order_by(GPTRuleCollectLogEntity.created_at.desc()).all())

diff_cnt = 0
for gpt_rule_collect_log_entity in gpt_rule_collect_log_entity_list:
    for rule_collect_instruction_message in gpt_rule_collect_log_entity.messages:
        session.add(MigrateRuleCollectInstructionMessageEntity.from_entity(rule_collect_instruction_message))
        session.flush()
session.commit()
print(f"result: {diff_cnt}")