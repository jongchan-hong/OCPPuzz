from typing import List

import pandas as pd
from datetime import datetime

from constants.category_map import CONSTRAINT_CATEGORY_MAP
from constants.error_code import ErrorCode
from rule_collector_modules.constraint_define import ConstraintDefine
from dataset.scripts.message_direction_result import MessageDirectionResult
from storage.entity.base_entity import session
from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.generate_rule_combination_entity import GenerateRuleCombinationEntity
import json
from storage.entity.test_execution_entity import TestExecutionEntity
from storage.loader.model_loader import ModelLoader
import os
from sqlalchemy import and_
loader = ModelLoader("storage.entity")
loader.load_models()
message_direction_result = MessageDirectionResult()


class ExpectResponseFormat():

    def __init__(self, message_type_id, error_code_list:List[ErrorCode] = None, token_status = None):
        self.message_type_id = message_type_id
        self.error_code_list:List[ErrorCode] = error_code_list
        self.token_status = token_status

    def get_expect_response(self):
        error_codes = ",".join([e.value for e in self.error_code_list]) if self.error_code_list else ""
        return self.message_type_id, error_codes

    def is_error_response(self, response):
        if not response:
            return False
        return response[0] == 4 and response[2] == "InternalError"


    def is_correct_response(self, response):
        if not response:
            return False
        if response[0] == 4 and response[2] in ["NotSupported", "NotImplemented"]:
            return True
        if self.message_type_id != response[0]:
            return False
        return True

CATEGORY_EXPECT_MAP = {
    "DataType": ExpectResponseFormat(4, [ErrorCode.TypeConstraintViolation, ErrorCode.FormatViolation]),
    "Presence": ExpectResponseFormat(4, [ErrorCode.FormatViolation, ErrorCode.PropertyConstraintViolation, ErrorCode.OccurrenceConstraintViolation]),
    "Content": ExpectResponseFormat(4, [ErrorCode.PropertyConstraintViolation, ErrorCode.OccurrenceConstraintViolation, ErrorCode.FormatViolation]),
    "Size": ExpectResponseFormat(4, [ErrorCode.OccurrenceConstraintViolation, ErrorCode.PropertyConstraintViolation, ErrorCode.FormatViolation]),
}
class AnalysisResult():
    def __init__(self, project_name, total_cnt, error_trigger_cnt, timeout_trigger_cnt, valid_timeout_trigger_cnt, invalid_timeout_trigger_cnt,timeout_trigger_description_rule_base_cnt, timeout_trigger_structural_rule_base_cnt,valid_seed_cnt, true_mismatch_cnt, true_validate_cnt, error_trigger_description_rule_base_cnt, error_trigger_structural_rule_base_cnt, unique_invalid_true_cnt, wrong_validate_cnt,wrong_validate_description_rule_base_cnt, wrong_validate_structural_rule_base_cnt, unique_wrong_validate_description_rule_base_cnt, unique_wrong_validate_structural_rule_base_cnt, unique_error_trigger_cnt, unique_timeout_trigger_cnt, unique_wrong_validate_cnt, unique_error_trigger_description_rule_base_cnt, unique_error_trigger_structural_rule_base_cnt, time_out_cnt, data_type_total_cnt,presence_total_cnt,content_total_cnt,size_total_cnt,data_type_wrong_validate_cnt,presence_wrong_validate_cnt,content_wrong_validate_cnt,size_wrong_validate_cnt):

        self.project_name = project_name
        self.total_cnt = total_cnt
        self.error_trigger_cnt = error_trigger_cnt
        self.error_trigger_description_rule_base_cnt = error_trigger_description_rule_base_cnt
        self.error_trigger_structural_rule_base_cnt = error_trigger_structural_rule_base_cnt
        self.wrong_validate_cnt = wrong_validate_cnt
        self.wrong_validate_description_rule_base_cnt = wrong_validate_description_rule_base_cnt
        self.wrong_validate_structural_rule_base_cnt = wrong_validate_structural_rule_base_cnt
        self.unique_wrong_validate_description_rule_base_cnt = unique_wrong_validate_description_rule_base_cnt
        self.unique_wrong_validate_structural_rule_base_cnt = unique_wrong_validate_structural_rule_base_cnt
        self.unique_error_trigger_cnt = unique_error_trigger_cnt
        self.unique_timeout_trigger_cnt= unique_timeout_trigger_cnt
        self.timeout_trigger_cnt = timeout_trigger_cnt
        self.valid_timeout_trigger_cnt = valid_timeout_trigger_cnt
        self.invalid_timeout_trigger_cnt = invalid_timeout_trigger_cnt
        self.timeout_trigger_description_rule_base_cnt = timeout_trigger_description_rule_base_cnt
        self.timeout_trigger_structural_rule_base_cnt = timeout_trigger_structural_rule_base_cnt
        self.unique_wrong_validate_cnt = unique_wrong_validate_cnt
        self.unique_error_trigger_description_rule_base_cnt = unique_error_trigger_description_rule_base_cnt
        self.unique_error_trigger_structural_rule_base_cnt = unique_error_trigger_structural_rule_base_cnt
        self.time_out_cnt = time_out_cnt
        self.valid_seed_cnt = valid_seed_cnt
        self.true_mismatch_cnt=true_mismatch_cnt
        self.true_validate_cnt = true_validate_cnt
        self.unique_invalid_true_cnt = unique_invalid_true_cnt
        self.data_type_total_cnt =data_type_total_cnt
        self.presence_total_cnt = presence_total_cnt
        self.content_total_cnt = content_total_cnt
        self.size_total_cnt = size_total_cnt
        self.data_type_wrong_validate_cnt = data_type_wrong_validate_cnt
        self.presence_wrong_validate_cnt = presence_wrong_validate_cnt
        self.content_wrong_validate_cnt = content_wrong_validate_cnt
        self.size_wrong_validate_cnt = size_wrong_validate_cnt

    def get_percent_rate(self, a, b):
        if b > 0:
            percent = (a / b) * 100
            return round(percent, 1)
        return 0

    def get_data_type_mismatch_rate(self):
        return self.get_percent_rate(self.data_type_wrong_validate_cnt, self.data_type_total_cnt)
    def get_presence_mismatch_rate(self):
        return self.get_percent_rate(self.presence_wrong_validate_cnt, self.presence_total_cnt)
    def get_content_mismatch_rate(self):
        return self.get_percent_rate(self.content_wrong_validate_cnt, self.content_total_cnt)
    def get_size_mismatch_rate(self):
        return self.get_percent_rate(self.size_wrong_validate_cnt, self.size_total_cnt)
    def get_true_mismatch_rate(self):
        return self.get_percent_rate(self.true_mismatch_cnt, self.true_validate_cnt+self.true_mismatch_cnt)
    def get_total_mismatch_rate(self):
        return self.get_percent_rate(result.wrong_validate_cnt, result.total_cnt)

class Validator(object):
    def __init__(self, test_id_list):
        self.test_id_list = test_id_list
        self.generate_message_entity_list = self.get_generate_message_entity_list(self.test_id_list)
        self.project_map = self.get_project_map()
        self.mismatch_rows = []
        self.mismatch_map = {}
        self.match_rows = []
        self.match_map = {}
        self.error_trigger_rows = []
        self.timeout_trigger_rows = []

    def get_project_map(self):
        project_names = (
            session.query(TestExecutionEntity.project_name)
            .filter(TestExecutionEntity.generate_message_id.in_([e.id for e in self.generate_message_entity_list]))
            .distinct()
            .all()
        )
        project_names = [p[0] if p[0] else "UNKNOWN" for p in project_names]

        project_map = {
            project_name: {
                "total_cnt": len(self.generate_message_entity_list),
                "time_out_cnt": 0,
                "error_trigger_cnt": 0,
                "error_trigger_description_rule_base_cnt": 0,
                "error_trigger_structural_rule_base_cnt": 0,
                "timeout_trigger_cnt": 0,
                "valid_timeout_trigger_cnt": 0,
                "invalid_timeout_trigger_cnt": 0,
                "timeout_trigger_description_rule_base_cnt": 0,
                "timeout_trigger_structural_rule_base_cnt": 0,
                "wrong_validate_cnt": 0,
                "wrong_validate_description_rule_base_cnt": 0,
                "wrong_validate_structural_rule_base_cnt": 0,
                "valid_seed_cnt": 0,
                "true_mismatch_cnt": 0,
                "true_validate_cnt": 0,
                "data_type_total_cnt": 0,
                "presence_total_cnt": 0,
                "content_total_cnt": 0,
                "size_total_cnt": 0,
                "data_type_wrong_validate_cnt": 0,
                "presence_wrong_validate_cnt": 0,
                "content_wrong_validate_cnt": 0,
                "size_wrong_validate_cnt": 0,
                "unique_generate_rule_combination_value_entity_set": set(),
                "unique_generate_rule_combination_value_entity_description_rule_base_set": set(),
                "unique_generate_rule_combination_value_entity_structural_rule_base_set": set(),
                "unique_invalid_true_set": set(),
                "unique_error_trigger_generate_rule_combination_value_entity_set": set(),
                "unique_error_trigger_generate_rule_combination_value_entity_description_rule_base_set": set(),
                "unique_error_trigger_generate_rule_combination_value_entity_structural_rule_base_set": set(),
                "unique_timeout_trigger_generate_rule_combination_value_entity_set": set(),
                "unique_timeout_trigger_generate_rule_combination_value_entity_description_rule_base_set": set(),
                "unique_timeout_trigger_generate_rule_combination_value_entity_structural_rule_base_set": set(),
            }
            for project_name in project_names
        }
        return project_map



    def get_generate_message_entity_list(self, test_id_list):
        cs_to_csms_request_message_name_list = message_direction_result.get_random_test_message_list()
        return (session.query(GenerateMessageEntity).filter(
            and_(
                GenerateMessageEntity.test_id.in_(test_id_list),
                GenerateMessageEntity.action.in_(cs_to_csms_request_message_name_list)
            )
        ).outerjoin(TestExecutionEntity, TestExecutionEntity.generate_message_id == GenerateMessageEntity.id)
                .outerjoin(GenerateRuleCombinationEntity, GenerateMessageEntity.generate_rule_combination_id == GenerateRuleCombinationEntity.id)
                .order_by(GenerateMessageEntity.created_at.desc()).all())

    def save_rows(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = f"results/{timestamp}"
        os.makedirs(result_dir, exist_ok=True)

        true_mismatch_rows = []
        true_match_rows = []
        if self.mismatch_rows:
            true_mismatch_rows = [data for data in self.mismatch_rows if data["reverse_rule"] == "None"]

            df = pd.DataFrame(self.mismatch_rows)
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            grouped = df.groupby(["project_name", "action"])

            for (project_name, action), group in grouped:
                safe_project_name = project_name.replace(" ", "_").replace("/", "_")
                safe_action = action.replace(" ", "_").replace("/", "_")
                filename = f"{result_dir}/{timestamp}_{safe_project_name}_{safe_action}_validation_mismatch.xlsx"
                group.to_excel(filename, index=False)

        if self.match_rows:
            true_match_rows = [data for data in self.match_rows if data["reverse_rule"] == "None"]
            df = pd.DataFrame(self.match_rows)
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            grouped = df.groupby(["project_name", "action"])

            for (project_name, action), group in grouped:
                safe_project_name = project_name.replace(" ", "_").replace("/", "_")
                safe_action = action.replace(" ", "_").replace("/", "_")
                filename = f"{result_dir}/{timestamp}_{safe_project_name}_{safe_action}_validation_match.xlsx"
                group.to_excel(filename, index=False)

        if true_match_rows:
            df = pd.DataFrame(true_match_rows)
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            filename = f"{result_dir}/{timestamp}_validation_true_match_summary.xlsx"

            with pd.ExcelWriter(filename) as writer:
                grouped = df.groupby("project_name")
                for project_name, group in grouped:
                    safe_project_name = project_name.replace(" ", "_").replace("/", "_")[:31]
                    group.to_excel(writer, sheet_name=safe_project_name, index=False)
                section_df = df.sort_values(by=["action", "name", "reverse_rule", "id", "project_name"])
                section_df.to_excel(writer, sheet_name="summary", index=False)

        if true_mismatch_rows:
            df = pd.DataFrame(true_mismatch_rows)
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            filename = f"{result_dir}/{timestamp}_validation_true_mismatch_summary.xlsx"

            with pd.ExcelWriter(filename) as writer:
                grouped = df.groupby("project_name")
                for project_name, group in grouped:
                    safe_project_name = project_name.replace(" ", "_").replace("/", "_")[:31]
                    group.to_excel(writer, sheet_name=safe_project_name, index=False)
                section_df = df.sort_values(by=["action", "name", "reverse_rule", "id", "project_name"])
                section_df.to_excel(writer, sheet_name="summary", index=False)

        if self.mismatch_map:
            df = pd.DataFrame(self.mismatch_map.values())
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            filename = f"{result_dir}/{timestamp}_validation_mismatch_summary.xlsx"

            with pd.ExcelWriter(filename) as writer:
                grouped = df.groupby("project_name")
                for project_name, group in grouped:
                    safe_project_name = project_name.replace(" ", "_").replace("/", "_")[:31]
                    group.to_excel(writer, sheet_name=safe_project_name, index=False)
                section_df = df.sort_values(by=["action", "name", "reverse_rule", "id", "project_name"])
                section_df.to_excel(writer, sheet_name="summary", index=False)

        if self.match_map:
            df = pd.DataFrame(self.match_map.values())
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])
            filename = f"{result_dir}/{timestamp}_validation_match_summary.xlsx"
            with pd.ExcelWriter(filename) as writer:
                grouped = df.groupby("project_name")
                for project_name, group in grouped:
                    safe_project_name = project_name.replace(" ", "_").replace("/", "_")[:31]
                    group.to_excel(writer, sheet_name=safe_project_name, index=False)
                section_df = df.sort_values(by=["action", "name", "reverse_rule", "id", "project_name"])
                section_df.to_excel(writer, sheet_name="summary", index=False)
        if self.error_trigger_rows:
            df = pd.DataFrame(self.error_trigger_rows)
            df = df.sort_values(by=["project_name", "action", "name", "reverse_rule", "id"])

            filename = f"{result_dir}/{timestamp}_validation_error_trigger.xlsx"

            with pd.ExcelWriter(filename) as writer:
                grouped = df.groupby("project_name")
                for project_name, group in grouped:
                    safe_project_name = project_name.replace(" ", "_").replace("/", "_")[:31]
                    group.to_excel(writer, sheet_name=safe_project_name, index=False)


    def analysis(self, debug:bool)-> List[AnalysisResult]:

        for generate_message_entity in self.generate_message_entity_list:
            for test_execution_entity in generate_message_entity.test_execution_list:
                if not test_execution_entity.response:
                    self.project_map[test_execution_entity.project_name]["time_out_cnt"] += 1
            expect_response_format = ExpectResponseFormat(message_type_id=3)

            if generate_message_entity.generate_rule_combination_entity.generate_message_fail_list:
                for generate_message_fail in generate_message_entity.generate_rule_combination_entity.generate_message_fail_list:
                    print(f"[FAIL] {generate_message_fail.exception} / {generate_message_fail.cause}")

            reverse_constraint = None
            condition_key = None
            reverse_rule = None
            name = None
            set_key = None
            category = None
            for generate_rule_combination_value_entity in generate_message_entity.generate_rule_combination_entity.generate_rule_combination_value_entity_list:
                if generate_rule_combination_value_entity.is_active == False:
                    reverse_rule = generate_rule_combination_value_entity.generate_rule_entity.to_dto()
                    reverse_constraint = generate_rule_combination_value_entity.generate_rule_entity.generate_constraint.to_dto()
                    condition_list = generate_rule_combination_value_entity.generate_rule_entity.generate_condition_list
                    condition_key = str(sorted([tuple(sorted(c.to_dto().__dict__.items()))for c in condition_list]))
                    name = f"{generate_rule_combination_value_entity.generate_rule_entity.object_name}.{generate_rule_combination_value_entity.generate_rule_entity.field_name}"
                    set_key = name + str(reverse_constraint)

                    category = CONSTRAINT_CATEGORY_MAP.get(ConstraintDefine.getConstraintEnum(reverse_constraint)) if reverse_constraint else ""
                    expect_response_format = CATEGORY_EXPECT_MAP.get(category)
                    if expect_response_format is None:
                        print(f"Unknown constraint: {reverse_constraint}")
                        exit()


            is_description_base = False
            is_structural_rule_base = False
            if reverse_rule:
                for cause in reverse_rule.causes:
                    if cause.name.endswith("description"):
                        is_description_base = True
                    else:
                        is_structural_rule_base = True

            for test_execution_entity in generate_message_entity.test_execution_list:
                if not reverse_rule:
                    self.project_map[test_execution_entity.project_name]["valid_seed_cnt"] += 1
                if test_execution_entity.error_name or expect_response_format.is_error_response(test_execution_entity.response):

                    if test_execution_entity.error_name and "Timeout" in test_execution_entity.error_name:
                        self.project_map[test_execution_entity.project_name]["timeout_trigger_cnt"] += 1
                        if not reverse_rule:
                            self.project_map[test_execution_entity.project_name]["valid_timeout_trigger_cnt"] += 1
                        else:
                            self.project_map[test_execution_entity.project_name]["invalid_timeout_trigger_cnt"] += 1
                        self.project_map[test_execution_entity.project_name][
                            "unique_timeout_trigger_generate_rule_combination_value_entity_set"].add(set_key)
                        self.timeout_trigger_rows.append({
                            "id": generate_message_entity.id,
                            "action": generate_message_entity.action,
                            "name": name,
                            "reverse_rule": str(reverse_rule),
                            "reverse_constraint": str(reverse_constraint),
                            "condition_key": str(condition_key),
                            "payload": generate_message_entity.payload,
                            "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                            "error_name": test_execution_entity.error_name,
                            "project_name": test_execution_entity.project_name
                        })
                        if reverse_rule:
                            if is_description_base:
                                self.project_map[test_execution_entity.project_name][
                                    "timeout_trigger_description_rule_base_cnt"] += 1
                                self.project_map[test_execution_entity.project_name][
                                    "unique_timeout_trigger_generate_rule_combination_value_entity_description_rule_base_set"].add(
                                    set_key)
                            if is_structural_rule_base:
                                self.project_map[test_execution_entity.project_name][
                                    "timeout_trigger_structural_rule_base_cnt"] += 1
                                self.project_map[test_execution_entity.project_name][
                                    "unique_timeout_trigger_generate_rule_combination_value_entity_structural_rule_base_set"].add(
                                    set_key)
                    else:
                        self.project_map[test_execution_entity.project_name]["error_trigger_cnt"] += 1
                        self.project_map[test_execution_entity.project_name]["unique_error_trigger_generate_rule_combination_value_entity_set"].add(set_key)
                        self.error_trigger_rows.append({
                            "id": generate_message_entity.id,
                            "action": generate_message_entity.action,
                            "name": name,
                            "reverse_rule": str(reverse_rule),
                            "reverse_constraint": str(reverse_constraint),
                            "condition_key": str(condition_key),
                            "payload": generate_message_entity.payload,
                            "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                            "error_name": test_execution_entity.error_name,
                            "project_name": test_execution_entity.project_name
                        })
                        if reverse_rule:
                            if is_description_base:
                                self.project_map[test_execution_entity.project_name]["error_trigger_description_rule_base_cnt"]+=1
                                self.project_map[test_execution_entity.project_name]["unique_error_trigger_generate_rule_combination_value_entity_description_rule_base_set"].add(set_key)
                            if is_structural_rule_base:
                                self.project_map[test_execution_entity.project_name]["error_trigger_structural_rule_base_cnt"] += 1
                                self.project_map[test_execution_entity.project_name]["unique_error_trigger_generate_rule_combination_value_entity_structural_rule_base_set"].add(set_key)
            for test_execution_entity in generate_message_entity.test_execution_list:
                match category:
                    case "DataType":
                        self.project_map[test_execution_entity.project_name]["data_type_total_cnt"] += 1
                    case "Presence":
                        self.project_map[test_execution_entity.project_name]["presence_total_cnt"] += 1
                    case "Content":
                        self.project_map[test_execution_entity.project_name]["content_total_cnt"] += 1
                    case "Size":
                        self.project_map[test_execution_entity.project_name]["size_total_cnt"] += 1

                expect_message_type_id, expect_error_code_list = expect_response_format.get_expect_response()
                key = (generate_message_entity.action, name, str(condition_key), str(reverse_constraint),
                       test_execution_entity.project_name)

                if  expect_response_format.is_correct_response(test_execution_entity.response):
                    self.match_rows.append({
                        "id": generate_message_entity.id,
                        "action": generate_message_entity.action,
                        "name": name,
                        "reverse_rule": str(reverse_rule),
                        "reverse_constraint": str(reverse_constraint),
                        "condition_key": str(condition_key),
                        "payload": generate_message_entity.payload,
                        "expect_message_type_id": expect_message_type_id,
                        "expect_error_code_list": expect_error_code_list,
                        "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                        "project_name": test_execution_entity.project_name
                    })

                    if key not in self.match_map:
                        self.match_map[key] = {
                            "id":generate_message_entity.id,
                            "action":generate_message_entity.action,
                            "name": name,
                            "reverse_rule": str(reverse_rule),
                            "reverse_constraint": str(reverse_constraint),
                            "payload": generate_message_entity.payload,
                            "expect_message_type_id": expect_message_type_id,
                            "expect_error_code_list": expect_error_code_list,
                            "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                            "category":  category,
                            "project_name": test_execution_entity.project_name
                        }
                    if not is_description_base and not is_structural_rule_base:
                        self.project_map[test_execution_entity.project_name]["true_validate_cnt"] += 1
                else:
                    self.mismatch_rows.append({
                        "id":generate_message_entity.id,
                        "action":generate_message_entity.action,
                        "name": name,
                        "reverse_rule": str(reverse_rule),
                        "reverse_constraint": str(reverse_constraint),
                        "condition_key": str(condition_key),
                        "payload": generate_message_entity.payload,
                        "expect_message_type_id": expect_message_type_id,
                        "expect_error_code_list": expect_error_code_list,
                        "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                        "project_name": test_execution_entity.project_name
                    })

                    if key not in self.mismatch_map:
                        self.mismatch_map[key] = {
                            "id":generate_message_entity.id,
                            "action":generate_message_entity.action,
                            "name": name,
                            "reverse_rule": str(reverse_rule),
                            "reverse_constraint": str(reverse_constraint),
                            "payload": generate_message_entity.payload,
                            "expect_message_type_id": expect_message_type_id,
                            "expect_error_code_list": expect_error_code_list,
                            "response": json.dumps(test_execution_entity.response, ensure_ascii=False),
                            "category":  category,
                            "project_name": test_execution_entity.project_name
                        }
                    self.project_map[test_execution_entity.project_name]["unique_generate_rule_combination_value_entity_set"].add(set_key if set_key else name)

                    if is_description_base:
                        self.project_map[test_execution_entity.project_name]["unique_generate_rule_combination_value_entity_description_rule_base_set"].add(set_key)
                        self.project_map[test_execution_entity.project_name]["wrong_validate_description_rule_base_cnt"] +=1
                    if is_structural_rule_base:
                        self.project_map[test_execution_entity.project_name]["unique_generate_rule_combination_value_entity_structural_rule_base_set"].add(set_key)
                        self.project_map[test_execution_entity.project_name]["wrong_validate_structural_rule_base_cnt"]+=1
                    if not is_description_base and not is_structural_rule_base:
                        self.project_map[test_execution_entity.project_name]["true_mismatch_cnt"] += 1
                        self.project_map[test_execution_entity.project_name]["unique_invalid_true_set"].add(set_key)
                    self.project_map[test_execution_entity.project_name]["wrong_validate_cnt"] += 1

                    match category:
                        case "DataType":
                            self.project_map[test_execution_entity.project_name]["data_type_wrong_validate_cnt"] += 1
                        case "Presence":
                            self.project_map[test_execution_entity.project_name]["presence_wrong_validate_cnt"] += 1
                        case "Content":
                            self.project_map[test_execution_entity.project_name]["content_wrong_validate_cnt"] += 1
                        case "Size":
                            self.project_map[test_execution_entity.project_name]["size_wrong_validate_cnt"] += 1

            if debug:
                print(f"name: {name}")
                print(f"reverse_rule: {reverse_rule}")
                print(f"constraint: {reverse_constraint}")
                print(f"payload: {generate_message_entity.payload}")
                print(f"response: {generate_message_entity.test_execution_entity.response}")
                for test_execution_entity in generate_message_entity.test_execution_list:
                    print(f"correct: {str(expect_response_format.is_correct_response(test_execution_entity.response))}")



        return [AnalysisResult(
            project_name=project_name,
            total_cnt= project_data["total_cnt"],
            error_trigger_cnt = project_data["error_trigger_cnt"],
            timeout_trigger_cnt = project_data["timeout_trigger_cnt"],
            valid_timeout_trigger_cnt = project_data["valid_timeout_trigger_cnt"],
            invalid_timeout_trigger_cnt = project_data["invalid_timeout_trigger_cnt"],
            timeout_trigger_description_rule_base_cnt = project_data["timeout_trigger_description_rule_base_cnt"],
            timeout_trigger_structural_rule_base_cnt=project_data["timeout_trigger_structural_rule_base_cnt"],
            valid_seed_cnt = project_data["valid_seed_cnt"],
            true_mismatch_cnt=project_data["true_mismatch_cnt"],
            true_validate_cnt=project_data["true_validate_cnt"],
            error_trigger_description_rule_base_cnt = project_data["error_trigger_description_rule_base_cnt"],
            error_trigger_structural_rule_base_cnt = project_data["error_trigger_structural_rule_base_cnt"],
            wrong_validate_cnt=project_data["wrong_validate_cnt"],
            wrong_validate_description_rule_base_cnt = project_data["wrong_validate_description_rule_base_cnt"],
            wrong_validate_structural_rule_base_cnt = project_data["wrong_validate_structural_rule_base_cnt"],
            unique_invalid_true_cnt = len(project_data["unique_invalid_true_set"]),
            unique_wrong_validate_description_rule_base_cnt = len(project_data["unique_generate_rule_combination_value_entity_description_rule_base_set"]),
            unique_wrong_validate_structural_rule_base_cnt = len(project_data["unique_generate_rule_combination_value_entity_structural_rule_base_set"]),
            unique_error_trigger_cnt=len(project_data["unique_error_trigger_generate_rule_combination_value_entity_set"]),
            unique_timeout_trigger_cnt=len(project_data["unique_timeout_trigger_generate_rule_combination_value_entity_set"]),
            unique_wrong_validate_cnt = len(project_data["unique_generate_rule_combination_value_entity_set"]),
            unique_error_trigger_description_rule_base_cnt = len(project_data["unique_error_trigger_generate_rule_combination_value_entity_description_rule_base_set"]),
            unique_error_trigger_structural_rule_base_cnt = len(project_data["unique_error_trigger_generate_rule_combination_value_entity_structural_rule_base_set"]),
            time_out_cnt= project_data["time_out_cnt"],
            data_type_total_cnt= project_data["data_type_total_cnt"],
            presence_total_cnt= project_data["presence_total_cnt"],
            content_total_cnt= project_data["content_total_cnt"],
            size_total_cnt= project_data["size_total_cnt"],
            data_type_wrong_validate_cnt= project_data["data_type_wrong_validate_cnt"],
            presence_wrong_validate_cnt= project_data["presence_wrong_validate_cnt"],
            content_wrong_validate_cnt= project_data["content_wrong_validate_cnt"],
            size_wrong_validate_cnt= project_data["size_wrong_validate_cnt"],
        ) for project_name, project_data in self.project_map.items()]

user_input = input("write your test id from test table >> (example: 1 2 3)")
numbers = list(map(int, user_input.split()))
validator_list = [
    Validator(numbers)
]
def get_origin_name(name):
    match name:
        case "Citrine":
            return "CitrineOS"
        case "maeve-csms":
            return "MaEVe"
        case "ocpp-go":
            return "ocpp-go"
        case "OCPPCore":
            return "OCPP.Core"
        case _:
            return None

for validator in validator_list:
    analysis_result = validator.analysis(False)
    analysis_result = sorted(analysis_result, key=lambda x: x.project_name.lower())
    # print(f"{name} & {result.total_cnt} & {result.true_mismatch_cnt} & {result.wrong_validate_structural_rule_base_cnt} & {result.wrong_validate_description_rule_base_cnt} & {result.wrong_validate_cnt} & {result.unique_invalid_true_cnt} & {result.unique_wrong_validate_structural_rule_base_cnt} & {result.unique_wrong_validate_description_rule_base_cnt} & {result.unique_wrong_validate_cnt} & {result.time_out_cnt} & {result.error_trigger_cnt}  \\\\ \\hline")
    print("mismatch valid seed talbe start ===")
    for result in analysis_result:
        print(
            f"{get_origin_name(result.project_name)} & {result.true_validate_cnt + result.true_mismatch_cnt}& {result.true_validate_cnt} & {result.true_mismatch_cnt} \\\\ \\hline")
    print("mismatch valid seed talbe end ===")
    print("===============================================================")
    print("===============================================================")
    print("mismatch totoal talbe start ===")
    for i, result in enumerate(analysis_result):
        if i != 0:
            print("\\hline")
        print(
            f"{get_origin_name(result.project_name)} & {result.true_mismatch_cnt}/{result.valid_seed_cnt} ({result.get_true_mismatch_rate()}\\%) & {result.valid_timeout_trigger_cnt} & {result.data_type_wrong_validate_cnt}/{result.data_type_total_cnt} ({result.get_data_type_mismatch_rate()}\\%) & {result.presence_wrong_validate_cnt}/{result.presence_total_cnt} ({result.get_presence_mismatch_rate()}\\%) & {result.content_wrong_validate_cnt}/{result.content_total_cnt} ({result.get_content_mismatch_rate()}\\%) & {result.size_wrong_validate_cnt}/{result.size_total_cnt} ({result.get_size_mismatch_rate()}\\%) & {result.invalid_timeout_trigger_cnt} & {result.wrong_validate_cnt}/{result.total_cnt} ({result.get_total_mismatch_rate()}\\%) \\\\")
    print("mismatch totoal talbe end ===")
    validator.save_rows()