from rule_collector_modules.condition_define import ConditionDefine, ConditionEnum
from rule_collector_modules.constraint_define import ConstraintDefine, ConstraintEnum
from dto.scenario_action_dto import ScenarioActionDTO
from generator_modules.payload_context import PayloadContext
from scenario_collector_modules.scenario_act_type import ScenarioActType
from dataset.scripts.descripitive_rule_result import DescriptiveRuleResult
from dataset.scripts.message_direction_result import MessageDirectionResult
from dataset.scripts.scenario_result import ScenarioResult
from dto.scenario_collect_dto import ScenarioCollectDTO
from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.scenario_test_detail_entity import ScenarioTestDetailEntity
from storage.entity.scenario_test_detail_set_entity import ScenarioTestDetailSetEntity
from storage.entity.scenario_test_entity import ScenarioTestEntity
from storage.entity.test_entity import TestEntity
from storage.entity.test_execution_entity import TestExecutionEntity
from kafka_modules.kafka_command_message import KafkaCommandMessage, KafkaCommandEnum

import traceback
from generator_modules.fix_value_container import FixValueContainer
from generator_modules.generator import Generator
import random
from storage.db_engine import engine
from test_controller_modules.test_project_controller.maeve_csms_event_controller import MaeveCsmsEventController
from test_controller_modules.test_project_controller.ocpp_core_event_controller import OCPPCoreEventController
from test_controller_modules.test_project_controller.ocpp_go_event_controller import OCPPGoController
from test_controller_modules.test_project_controller.citrine_event_controller import CitrineEventController
from storage.entity.base_entity import Base
from sqlalchemy.orm import sessionmaker

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class TestControllerManager:
    MAX_RE_CONNECT = 10

    def __init__(self, config, parser, json_schemas, loop):
        print("[TestControllerManager] init")
        self.config = config
        self.parser = parser
        self.json_schemas = json_schemas
        self.message_direction_result = MessageDirectionResult()
        self.scenario_result = ScenarioResult()
        self.descriptive_rule_result: DescriptiveRuleResult = DescriptiveRuleResult()
        self.loop = loop
        self.current_test_execution_entity_id = None
        self.project_event_controller_list = self.get_project_event_controller_list()


    def get_project_event_controller_list(self):
        project_list = [
            # CitrineEventController(test_controller_manager=self),
            # OCPPCoreEventController(test_controller_manager=self),
            # MaeveCsmsEventController(test_controller_manager=self),
            # OCPPGoController(test_controller_manager=self)
        ]
        result = []
        for project_event_controller in project_list:
            if project_event_controller.connect():
                print(f"[TestControllerManager] Add {project_event_controller.project_name} Project")
                result.append(project_event_controller)
            else:
                print(f"[TestControllerManager] Cannot Add {project_event_controller.project_name} Project")
        return result

    async def command_process(self, command_message:KafkaCommandMessage):
        try:
            for project_event_controller in self.project_event_controller_list:
                project_event_controller.coverage_init()
            match command_message.command:
                case KafkaCommandEnum.RANDOM:
                    await self.random_generation_test(command_message)
                case KafkaCommandEnum.RULE_BASED_RANDOM:
                    await self.rule_based_random_test(command_message)
                case KafkaCommandEnum.RULE_BASED_SCENARIO:
                    await self.scenario_test(command_message)
                case _:
                    print("unknown command")
        except Exception as e:
            traceback.print_exc()
            print(e)

    async def scenario_test(self, command_message:KafkaCommandMessage):
        session = SessionLocal()
        try:
            for i in range(command_message.gen_cnt):
                test_entity = TestEntity(cause="scenario test")
                session.add(test_entity)
                session.flush()
                for project_event_controller in self.project_event_controller_list:
                    project_event_controller.test_entity = test_entity
                scenario_set = self.scenario_result.get_scenario_set(parser=self.parser, json_schemas=self.json_schemas)
                print(f"[Test Controller Manager] scenario_set cnt:: {len(scenario_set)}")

                scenario_test_entity = ScenarioTestEntity()
                session.add(scenario_test_entity)
                count = 0
                for scenario_collect_dto in scenario_set:
                    count += 1
                    await self.scenario_test_init(scenario_collect_dto, scenario_test_entity, command_message, test_entity, session)
                print(print(f"[Test Controller Manager] real scenario_set cnt:: {count}"))
                for project_event_controller in self.project_event_controller_list:
                    project_event_controller.save_total_coverage(test_entity, session)
        except Exception as e:
            session.rollback()
            print("scenario_test error:", e)
            traceback.print_exc()
        finally:
            session.close()

    def set_variables(self, scenario_collect_dto, scenario_test_detail_entity, session):
        if scenario_collect_dto.pre_configuration_variable_list:
            set_variable_data_list = scenario_collect_dto.get_set_variable_data_list()
            scenario_test_detail_entity.pre_configuration = str(set_variable_data_list)
            session.commit()
            for project_event_controller in self.project_event_controller_list:
                project_event_controller.set_variables(set_variable_data_list=set_variable_data_list)

    async def scenario_test_init(self, scenario_collect_dto: ScenarioCollectDTO, scenario_test_entity: ScenarioTestEntity, command_message:KafkaCommandMessage, test_entity, session):
        scenario_test_detail_entity = ScenarioTestDetailEntity(
            scenario_test_id=scenario_test_entity.id,
            scenario_test_entity=scenario_test_entity,
            scenario_collect_info = str(scenario_collect_dto.to_json())
        )
        session.add(scenario_test_detail_entity)
        session.commit()

        action_list = self.get_scenario_action_list(scenario_collect_dto.scenario_list, test_entity, session)
        await self.generate_stepwise_combinations_test(action_list, scenario_test_detail_entity, test_entity, scenario_collect_dto, session)

    async def reconnect_project_controller(self, cs_id):
        for project_event_controller in self.project_event_controller_list:
            project_event_controller.reconnect(cs_id)


    async def generate_stepwise_combinations_test(self, action_list, scenario_test_detail_entity: ScenarioTestDetailEntity, test_entity, scenario_collect_dto, session):
        result = []

        generator_indices = [i for i, a in enumerate(action_list) if
                             a.scenario_act_type == ScenarioActType.CS_TO_CSMS_REQUEST]


        for step_idx, gen_idx in enumerate(generator_indices):
            gen = action_list[gen_idx]
            for combo in gen.generator.combinations:
                determine_rule = None
                determine_rule_entity = None
                for generate_rule_entity, is_active in combo.items():
                    if is_active == False:
                        determine_rule = generate_rule_entity.to_dto()
                        determine_rule_entity = generate_rule_entity

                row = []
                try:
                    scenario_test_detail_set_entity = ScenarioTestDetailSetEntity(
                        scenario_test_detail_id=scenario_test_detail_entity.id,
                        scenario_test_detail_entity=scenario_test_detail_entity
                    )
                    session.add(scenario_test_detail_set_entity)
                    session.commit()
                    await self.reconnect_project_controller(f"SCENARIO_{scenario_test_detail_set_entity.id}")

                    self.set_variables(scenario_collect_dto=scenario_collect_dto,
                                       scenario_test_detail_entity=scenario_test_detail_entity,
                                       session=session
                    )

                    seqNo = 0
                    context = PayloadContext()
                    context.set_variable_data_list(scenario_collect_dto.get_set_variable_data_list())
                    act_prepare_once = False
                    for i in range(gen_idx + 1):

                        context.refresh()
                        action = action_list[i]
                        try:
                            match action.scenario_act_type:
                                case ScenarioActType.CS_TO_CSMS_REQUEST:
                                    await self.set_fix_value(action, context, seqNo)
                                    seqNo += 1
                                    generate_message_entity = None
                                    if i == gen_idx and gen.generator == action.generator:
                                        generate_message_entity = action.generator.generate_message_entity(combo, context)
                                    else:
                                        if i < gen_idx:
                                            if determine_rule:
                                                if determine_rule.conditions:
                                                    for condition in determine_rule.conditions:
                                                        match ConditionDefine.getConditionEnum(condition):
                                                            case ConditionEnum.VALUE_EQUAL:
                                                                pass
                                                            case ConditionEnum.IS_FIRST_TRANSACTION_EVENT_AFTER_EV_CONNECTION_EQUAL_FALSE:
                                                                print(action.generator.message_name)
                                                                if action.generator.message_name == "TransactionEventRequest" and not act_prepare_once:
                                                                    context.set_ev_connection_trigger(True)
                                                                    act_prepare_once = True
                                                            case _:
                                                                pass
                                                match ConstraintDefine.getConstraintEnum(determine_rule.constraint):
                                                    case ConstraintEnum.ONCE_PER_TRANSACTION_EQUAL_TRUE:
                                                        if action.generator.message_name == "TransactionEventRequest" and not act_prepare_once:
                                                            if determine_rule_entity.field_name == "reservationId":
                                                                context.required_reservation_id()
                                                                act_prepare_once = True
                                                            elif determine_rule_entity.field_name == "idToken":
                                                                context.required_id_token()
                                                                context.set_force_event_type("Started")
                                                                act_prepare_once = True
                                        generate_message_entity = action.generator.generate_true_message_entity(context)

                                    if not generate_message_entity:
                                        scenario_test_detail_set_entity.fail_cause = "CS_TO_CSMS_REQUEST Generate Fail"
                                        session.commit()
                                        continue
                                    scenario_test_detail_set_entity.generate_message_list.append(generate_message_entity)
                                    context.generate_message_entity_list.append(generate_message_entity)
                                    session.commit()
                                    tasks = []

                                    for project_event_controller in self.project_event_controller_list:
                                        try:
                                            test_execution_entity = TestExecutionEntity(
                                                generate_message_entity=generate_message_entity,
                                                project_name=project_event_controller.project_name
                                            )
                                            session.add(test_execution_entity)
                                            session.commit()
                                            self.current_test_execution_entity_id = test_execution_entity.id
                                            if not project_event_controller.connected:
                                                print(f"[{project_event_controller.project_name}][Error] Connection Fail")
                                                project_event_controller.reconnect()
                                                if not project_event_controller.connected:
                                                    continue
                                            await project_event_controller.send_message_and_wait(test_execution_entity, session)
                                        except Exception as controller_exception:
                                            print(f"[ERROR][TestControllerManager][{project_event_controller.project_name}]: {controller_exception}")
                                            continue

                                case ScenarioActType.CS_TO_CSMS_RESPONSE:
                                    generate_message_entity = action.generator.generate_true_message_entity(context)
                                    scenario_test_detail_set_entity.generate_message_list.append(generate_message_entity)

                                    tasks = []

                                    for project_event_controller in self.project_event_controller_list:
                                        try:
                                            if not project_event_controller.connected:
                                                print(f"[{project_event_controller.project_name}][Error] Connection Fail")
                                                project_event_controller.reconnect()
                                                if not project_event_controller.connected:
                                                    continue
                                            project_event_controller.send_message(generate_message_entity.get_call_result_json())
                                        except Exception as controller_exception:
                                            print(
                                                f"[ERROR][TestControllerManager][{project_event_controller.project_name}]: {controller_exception}")
                                            continue
                                case ScenarioActType.CSMS_TO_CS_REQUEST:
                                    generate_message_entity = action.generator.generate_true_message_entity(context)
                                    if not generate_message_entity:
                                        scenario_test_detail_set_entity.fail_cause = "CSMS_TO_CS_REQUEST Generate Fail"
                                        session.commit()
                                        continue
                                    evse_id = generate_message_entity.patch_payload(context)

                                    if evse_id:
                                        for project_event_controller in self.project_event_controller_list:
                                            try:
                                                project_event_controller.set_evse_id(evse_id)
                                            except Exception as controller_exception:
                                                print(
                                                    f"[ERROR][TestControllerManager][{project_event_controller.project_name}]: {controller_exception}")
                                                continue
                                    context.generate_message_entity_list.append(generate_message_entity)
                                    scenario_test_detail_set_entity.generate_message_list.append(generate_message_entity)

                                    if action.generator.message_name == "SetVariablesRequest":
                                        dict = generate_message_entity.get_payload_dict()
                                        context.set_variable_data_list(dict["setVariableData"])
                                    tasks = []

                                    for project_event_controller in self.project_event_controller_list:
                                        try:
                                            if not project_event_controller.support_csms_to_cs_trigger:
                                                continue
                                            if not project_event_controller.connected:
                                                project_event_controller.reconnect()
                                                if not project_event_controller.connected:
                                                    continue
                                            await project_event_controller.send_trigger_and_wait(generate_message_entity, session)
                                        except Exception as controller_exception:
                                            print(
                                                f"[ERROR][TestControllerManager][{project_event_controller.project_name}]: {controller_exception}")
                                            continue
                                case _:
                                    row.append(str(action))
                        except Exception as inner_e:
                            print(f"[ERROR][TestControllerManager][Action][{action.scenario_act_type}] combo={combo}: {inner_e}")
                            traceback.print_exc()
                            continue
                    result.append(row)
                except Exception as e:
                    session.rollback()
                    print("[ERROR][TestControllerManager][generate_stepwise_combinations_test]:", e)
                    traceback.print_exc()
        return result

    async def is_first_transaction_event_after_authorization(self, condition):
        return condition.target == "context.isFirstTransactionEventAfterAuthorization" and condition.values[0] == "true"

    async def set_fix_value(self, action, context, seqNo):
        if action.generator.message_name == "TransactionEventRequest":
            action.generator.fix_value_container.set_value(
                parent_key="TransactionEventRequest",
                field_name="seqNo",
                value=seqNo
            )
        transaction_id = context.get_saved_transaction_id()
        if transaction_id:
            action.generator.fix_value_container.set_value(
                parent_key="transactionInfo",
                field_name="transactionId",
                value=transaction_id
            )

    def get_scenario_action_list(self, scenario_list, test_entity, session):
        action_list = []
        for scenario in scenario_list:
            match ScenarioActType.get_act_type(scenario):
                case ScenarioActType.CS_TO_CSMS_REQUEST:
                    action_list.append(ScenarioActionDTO(
                        scenario_act_type=ScenarioActType.CS_TO_CSMS_REQUEST,
                        generator=Generator(
                            config=self.config,
                            message_name=scenario.message,
                            json_schema=self.json_schemas.get(scenario.message),
                            descriptive_rule_result=self.descriptive_rule_result,
                            parser=self.parser,
                            fix_value_container=scenario.get_fix_value_container(),
                            test_controller_manager=self,
                            test_entity_id = test_entity.id,
                            session = session
                        )
                    ))
                case ScenarioActType.CS_TO_CSMS_RESPONSE:
                    action_list.append(ScenarioActionDTO(
                        scenario_act_type=ScenarioActType.CS_TO_CSMS_RESPONSE,
                        generator=Generator(
                            config=self.config,
                            message_name=scenario.message,
                            json_schema=self.json_schemas.get(scenario.message),
                            descriptive_rule_result=self.descriptive_rule_result,
                            parser=self.parser,
                            fix_value_container=scenario.get_fix_value_container(),
                            test_controller_manager=self,
                            test_entity_id = test_entity.id,
                            session=session
                        )
                    ))
                    pass
                case ScenarioActType.CSMS_TO_CS_REQUEST:
                    action_list.append(ScenarioActionDTO(
                        scenario_act_type=ScenarioActType.CSMS_TO_CS_REQUEST,
                        generator=Generator(
                            config=self.config,
                            message_name=scenario.message,
                            json_schema=self.json_schemas.get(scenario.message),
                            descriptive_rule_result=self.descriptive_rule_result,
                            parser=self.parser,
                            fix_value_container=scenario.get_fix_value_container(),
                            test_controller_manager=self,
                            test_entity_id = test_entity.id,
                            session=session
                        )
                    ))
                case ScenarioActType.CSMS_TO_CS_RESPONSE | _:
                    pass
        return action_list

    def insert_id_token(self, id_token, type):
        for project_event_controller in self.project_event_controller_list:
            try:
                project_event_controller.insert_token(id_token, type)
            except Exception as e:
                pass


    async def random_generation_test(self, kafka_command_message: KafkaCommandMessage):
        session = SessionLocal()
        try:
            test_entity = TestEntity(cause="random generation test")
            session.add(test_entity)
            session.commit()
            test_cnt = 0

            while test_cnt < kafka_command_message.gen_cnt:
                random_message_name = random.choice(self.message_direction_result.get_random_test_message_list())
                generator = Generator(
                    config=self.config,
                    message_name=random_message_name,
                    json_schema=self.json_schemas.get(random_message_name),
                    descriptive_rule_result=self.descriptive_rule_result,
                    parser=self.parser,
                    fix_value_container=FixValueContainer(),
                    test_controller_manager=self,
                    gen_cnt=1,
                    rule_collection_flag=False,
                    test_entity_id = test_entity.id,
                    session=session
                )
                generate_message_entity: GenerateMessageEntity = generator.generate_true_message_entity(context=PayloadContext())
                if generate_message_entity:
                    test_cnt += 1
                    print(f"test cnt: {test_cnt}")
                    for project_event_controller in self.project_event_controller_list:
                        test_execution_entity = TestExecutionEntity(
                            generate_message_entity=generate_message_entity,
                            project_name=project_event_controller.project_name
                        )
                        session.add(test_execution_entity)
                        session.commit()
                        project_event_controller.reconnect(f"RANDOM_{generate_message_entity.id}")
                        self.current_test_execution_entity_id = test_execution_entity.id
                        if not project_event_controller.connected:
                            print(f"[{project_event_controller.project_name}][Error] Connection Fail")
                            continue
                        await project_event_controller.send_message_and_wait(test_execution_entity, session)
                    session.commit()
                if test_cnt >= kafka_command_message.gen_cnt:
                    break
            for project_event_controller in self.project_event_controller_list:
                project_event_controller.save_total_coverage(test_entity, session)

        except Exception as e:
            session.rollback()
            print("[ERROR][TestControllerManager]random_generateion_tet error:", e)
        finally:
            session.close()
            print(f"[TestControllerManager] randmom_generation_test End")

    async def rule_based_random_test(self, kafka_command_message: KafkaCommandMessage):
        session = SessionLocal()
        try:
            test_entity = TestEntity(cause="rule based random")
            session.add(test_entity)
            session.commit()
            await self.rule_base_random_test_send(kafka_command_message, test_entity, session)
            for project_event_controller in self.project_event_controller_list:
                project_event_controller.save_total_coverage(test_entity, session)
        except Exception as e:
            traceback.print_exc()
            session.rollback()
            print("rule_based_random_test:", e)
        finally:
            session.close()
            print(f"[TestControllerManager] rule_based_random_test End")


    async def rule_base_random_test_send(self, kafka_command_message, test_entity, session):
        test_cnt = 0
        message_list = self.message_direction_result.get_random_test_message_list()
        while test_cnt < kafka_command_message.gen_cnt:
            for message in message_list:
                generator = Generator(
                    config=self.config,
                    message_name=message,
                    json_schema=self.json_schemas.get(message),
                    descriptive_rule_result=self.descriptive_rule_result,
                    parser=self.parser,
                    fix_value_container=FixValueContainer(),
                    test_controller_manager=self,
                    gen_cnt=1,
                    test_entity_id = test_entity.id,
                    session=session
                )
                for combo in generator.combinations:
                    try:
                        generate_message_entity = generator.generate_message_entity(combo, PayloadContext())

                        if generate_message_entity:
                            test_cnt += 1
                            print(f"test cnt: {test_cnt}")
                            print(f"kafka_command_message.gen_cnt: {kafka_command_message.gen_cnt}")

                            for project_event_controller in self.project_event_controller_list:
                                test_execution_entity = TestExecutionEntity(
                                    generate_message_entity=generate_message_entity,
                                    project_name=project_event_controller.project_name
                                )
                                session.add(test_execution_entity)
                                session.commit()
                                project_event_controller.reconnect(f"RULE_RANDOM_{generate_message_entity.id}")
                                self.current_test_execution_entity_id = test_execution_entity.id
                                if not project_event_controller.connected:
                                    print(f"[{project_event_controller.project_name}][Error] Connection Fail")
                                    continue
                                await project_event_controller.send_message_and_wait(test_execution_entity, session)
                        else:
                            print("generate_message_entity fail")
                        if test_cnt >= kafka_command_message.gen_cnt:
                            return
                    except Exception as e:
                        session.rollback()
                        print("[ERROR][TestControllerManager][rule_base_random_test_send]:", e)
    def report_error(self, error_name):
        if self.current_test_execution_entity_id:
            session = SessionLocal()
            try:
                entity = session.query(TestExecutionEntity).get(self.current_test_execution_entity_id)
                if entity:
                    entity.error_name = error_name
                    session.commit()
            except Exception as e:
                session.rollback()
                print(f"Report error fail: {e}")
            finally:
                session.close()
