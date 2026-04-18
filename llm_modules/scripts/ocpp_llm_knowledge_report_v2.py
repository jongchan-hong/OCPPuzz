from storage.entity.llm_knowledge_collect_entity import LLMKnowledgeCollectEntity
from parser_modules.parser import Parser
from constants.version_config import version201, Config

from parser_modules.json.json_schema import get_json_schemas
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import json
from storage.entity.base_entity import session
from storage.loader.model_loader import ModelLoader

mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
loader = ModelLoader("storage.entity")
loader.load_models()

llm_knowledge_collect_id_list = [17]
llm_knowledge_collect_entity_list = session.query(LLMKnowledgeCollectEntity).filter(
        LLMKnowledgeCollectEntity.id.in_(llm_knowledge_collect_id_list)
).all()
config:Config = version201
json_schemas = get_json_schemas(config.json_schema_folder_path)
parser = Parser(config)
result = {}
result['message'] = {}
result['class'] = {}
objects = parser.messages + parser.data_types

def is_same_express_type(response_type, pdf_type):
    if response_type == "string" and pdf_type == "dateTime":
        return True
    if response_type + "Type" == pdf_type:
        return True
    if pdf_type == "decimal" and response_type in ["float", "double"]:
        return True
    if "integer" in pdf_type and "integer" in response_type:
        return True
    if pdf_type.endswith("EnumType") and response_type == "string":
        return True
    return False

def is_same_express_card(response_card, pdf_card):
    if response_card == "1..n" and pdf_card == "1..*":
        return True
    return False

def get_graph_model_name(model):
    match model:
        case "llama3"|"llama4":
            return model.capitalize()
        case "gemma3:27b":
            return "Gemma3"
        case "gpt-4o":
            return "GPT‑4o"
    return None


for llm_knowledge_collect_entity in llm_knowledge_collect_entity_list:
    for llm_knowledge_collect_detail_entity in llm_knowledge_collect_entity.detail_list:
        try:
            group_name = "message" if llm_knowledge_collect_detail_entity.object_name.endswith("Request") or llm_knowledge_collect_detail_entity.object_name.endswith(
                "Response") else "class"

            if llm_knowledge_collect_detail_entity.model not in result[group_name]:
                result[group_name][llm_knowledge_collect_detail_entity.model] = {
                    "total_spec_precision_cnt": 0,
                    "total_spec_precision_true_cnt": 0,
                    "total_spec_recall_cnt": 0,
                    "total_spec_recall_true_cnt": 0
                }

            object_data = [obj for obj in objects if obj.name == llm_knowledge_collect_detail_entity.object_name][0]
            receive_field_info_list = [receive_field_info for receive_field_info in json.loads(llm_knowledge_collect_detail_entity.response) if
                                                 receive_field_info["name"] != "customData"]
            for field in object_data.fields:

                data_type_total_spec_precision_cnt = len(object_data.fields)
                result[group_name][llm_knowledge_collect_detail_entity.model]["total_spec_precision_cnt"] += data_type_total_spec_precision_cnt

                data_type_total_receive_cnt = len(receive_field_info_list)
                result[group_name][llm_knowledge_collect_detail_entity.model]["total_spec_recall_cnt"] += data_type_total_receive_cnt


                match_receive_field_info_list = [receive_field_info for receive_field_info in receive_field_info_list if
                                                 receive_field_info["name"] == field.name]
                if not len(match_receive_field_info_list) > 0:
                    continue
                match_receive_field = match_receive_field_info_list[0]
                is_match = True

                if match_receive_field.get("type") == field.type or is_same_express_type (match_receive_field.get("type"), field.type):
                    pass
                else:
                    is_match = False

                if match_receive_field.get("card") == field.card or is_same_express_card(match_receive_field.get("card"), field.card):
                    pass
                else:
                    is_match = False
                if is_match:
                    result[group_name][llm_knowledge_collect_detail_entity.model]["total_spec_precision_true_cnt"] += 1

            for receive_field_info in receive_field_info_list:
                match_data_type_field_list = [field for field in object_data.fields if
                                              receive_field_info["name"] == field.name]
                if not len(match_data_type_field_list) > 0:
                    continue
                match_field = match_data_type_field_list[0]
                is_match = True
                if receive_field_info.get("type") == match_field.type or is_same_express_type (receive_field_info.get("type"), match_field.type):
                    pass
                else:
                    is_match = False
                if receive_field_info.get("card") == match_field.card or is_same_express_card(receive_field_info.get("card"), match_field.card):
                    pass
                else:
                    is_match = False
                if is_match:
                    result[group_name][llm_knowledge_collect_detail_entity.model]["total_spec_recall_true_cnt"] += 1

        except json.JSONDecodeError:
            print("json decode error")
            continue







def make_graph(type_name, result_data):
    models = []
    precisions = []
    recalls = []
    temp = []

    for model, stats in result_data.items():
        prec = (
            stats["total_spec_precision_true_cnt"] / stats["total_spec_precision_cnt"] * 100
            if stats["total_spec_precision_cnt"] > 0 else 0
        )
        rec = (
            stats["total_spec_recall_true_cnt"] / stats["total_spec_recall_cnt"] * 100
            if stats["total_spec_recall_cnt"] > 0 else 0
        )
        temp.append((model, prec, rec, prec + rec))


    temp.sort(key=lambda x: x[3], reverse=True)


    for model, prec, rec, _ in temp:
        models.append(get_graph_model_name(model))
        precisions.append(prec)
        recalls.append(rec)
    precision_color = '#4269D0FF'
    recall_color = '#3CA951FF'

    bar_height = 0.45
    index = np.arange(len(models))
    alpha = 0.9

    fig, ax = plt.subplots(figsize=(5, 3))

    bars1 = ax.barh(index + bar_height / 2, precisions, bar_height,
                    color=precision_color, alpha=alpha, label='Precision', edgecolor='#444444')
    bars2 = ax.barh(index - bar_height / 2, recalls, bar_height,
                    color=recall_color, alpha=alpha, label='Recall', edgecolor='#444444')

    def add_labels_horizontal(bars):
        for bar in bars:
            print(bar)
            width = bar.get_width()
            ax.annotate(f'{width:.1f}%',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0),
                        textcoords="offset points",
                        ha='left', va='center',
                        fontsize=9)

    add_labels_horizontal(bars1)
    add_labels_horizontal(bars2)

    ax.set_xlabel('Accuracy (%)', fontsize=9, fontweight='bold')
    ax.set_ylabel('Model', fontsize=9, fontweight='bold')
    ax.set_yticks(index)
    ax.set_yticklabels(models, fontsize=9)
    ax.set_xlim(0, 100)
    ax.legend(fontsize=9)
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(f"re_llm_precision_{type_name}_recall_horizontal.pdf", dpi=300, format="pdf", bbox_inches="tight")
    print(f"✅ Saved: llm_precision_{type_name}_recall_horizontal.pdf")

for type, model in result.items():
    make_graph(type, model)
exit()


plt.show()

field_rule_list = field.get_field_rule_list()
combination_list = get_combination_list(field_rule_list)
for combination in combination_list:
    rule_config = RuleConfig()
    for field_rule in field_rule_list:
        if not field_rule.check_pre_condition():
            continue
        if field_rule.is_reverse_rule_combination(combination):
            field_rule.reverse()
        rule_config.add(field_rule)
    if rule_config.is_uncreateable():
        continue
    field_value = make_random_value(rule_config)


    



