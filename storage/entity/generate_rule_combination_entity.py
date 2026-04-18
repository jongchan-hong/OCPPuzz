from sqlalchemy.orm import relationship

from storage.entity.base_entity import BaseEntity
from sqlalchemy import Column, Integer, ForeignKey

from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.generate_message_fail_entity import GenerateMessageFailEntity
from storage.entity.generate_rule_combination_value_entity import GenerateRuleCombinationValueEntity


class GenerateRuleCombinationEntity(BaseEntity):
    __tablename__ = 'generate_rule_combination'

    generate_id = Column(Integer, ForeignKey('generate.id'))
    generate_entity = relationship("GenerateEntity", back_populates="generate_rule_combination_list")

    generate_rule_combination_value_entity_list = relationship(
        argument=GenerateRuleCombinationValueEntity,
        back_populates="generate_rule_combination_entity",
        cascade="all, delete-orphan"
    )

    generate_message_list = relationship(
        argument=GenerateMessageEntity,
        back_populates="generate_rule_combination_entity",
        cascade="all, delete-orphan"
    )

    generate_message_fail_list = relationship(
        argument=GenerateMessageFailEntity,
        back_populates="generate_rule_combination_entity",
        cascade="all, delete-orphan"
    )

    def __init__(self, generate_entity, combination):
        super().__init__()
        self.generate_entity = generate_entity
        for generate_rule_entity, is_active in combination.items():
            self.generate_rule_combination_value_entity_list.append(
                GenerateRuleCombinationValueEntity(
                    generate_rule_combination_entity = self,
                    generate_rule_entity = generate_rule_entity,
                    is_active = is_active
                )
            )