from storage.entity.coverage_metric_entity import CoverageType, CoverageMetricEntity

from storage.entity.coverage_info_entity import CoverageInfoEntity
from storage.entity.base_entity import session
from sqlalchemy import and_, func
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
from storage.loader.model_loader import ModelLoader
loader = ModelLoader("storage.entity")
loader.load_models()
random_coverage_info_target_id = 0
random_coverage_info_last_id =0

scenario_coverage_info_start_id = 1
scenario_coverage_info_end_id = 57875
scenario_coverage_info_entity_list = session.query(CoverageInfoEntity).filter(
    and_(
        CoverageInfoEntity.id >= scenario_coverage_info_start_id,
        CoverageInfoEntity.id <= scenario_coverage_info_end_id
    )
).order_by(CoverageInfoEntity.id).all()
print(f"scenario random: {len(scenario_coverage_info_entity_list)}")
rule_random_coverage_info_entity_list = session.query(CoverageInfoEntity).filter(
    and_(
        CoverageInfoEntity.id >= scenario_coverage_info_end_id+1
    )
).order_by(CoverageInfoEntity.id).limit(len(scenario_coverage_info_entity_list)).all()
print(f"rule random: {len(rule_random_coverage_info_entity_list)}")

random_coverage_info_entity_list = session.query(CoverageInfoEntity).filter(
    and_(
        CoverageInfoEntity.id >= 134568
    )
).order_by(CoverageInfoEntity.id).limit(len(scenario_coverage_info_entity_list)).all()
print(f"random: {len(random_coverage_info_entity_list)}")
rule_random_coverage_metric_dict = {}
random_coverage_metric_dict = {}
print(f"len(scenario_coverage_info_entity_list) {len(scenario_coverage_info_entity_list)}")


max_branch_total_random = session.query(func.max(CoverageMetricEntity.total)).join(CoverageInfoEntity).filter(
    and_(
        CoverageInfoEntity.id >= random_coverage_info_target_id,
        CoverageInfoEntity.id <= random_coverage_info_last_id,
        CoverageMetricEntity.type == CoverageType.BRANCHES
    )
).scalar()

max_branch_total_scenario = session.query(func.max(CoverageMetricEntity.total)).join(CoverageInfoEntity).filter(
    and_(
        CoverageInfoEntity.id >= scenario_coverage_info_start_id,
        CoverageMetricEntity.type == CoverageType.BRANCHES
    )
).scalar()

max_branch_total = max(max_branch_total_random or 0, max_branch_total_scenario or 0)


def get_coverage_value(coverage_metric_entity):
    match coverage_metric_entity.type.value:
        case CoverageType.BRANCHES.value:
            return coverage_metric_entity.covered/max_branch_total * 100
        case _:
            return coverage_metric_entity.pct

random_coverage_metric_dict = {}
for coverage_info_entity in random_coverage_info_entity_list:
    for coverage_metric_entity in coverage_info_entity.coverage_metric_list:
        if coverage_metric_entity.type.value not in random_coverage_metric_dict:
            random_coverage_metric_dict[coverage_metric_entity.type.value] = []
        random_coverage_metric_dict[coverage_metric_entity.type.value].append(get_coverage_value(coverage_metric_entity))

for coverage_info_entity in rule_random_coverage_info_entity_list:
    for coverage_metric_entity in coverage_info_entity.coverage_metric_list:
        if coverage_metric_entity.type.value not in rule_random_coverage_metric_dict:
            rule_random_coverage_metric_dict[coverage_metric_entity.type.value] = []
        rule_random_coverage_metric_dict[coverage_metric_entity.type.value].append(get_coverage_value(coverage_metric_entity))

scenario_coverage_metric_dict = {}

for coverage_info_entity in scenario_coverage_info_entity_list:
    for coverage_metric_entity in coverage_info_entity.coverage_metric_list:
        if coverage_metric_entity.type.value not in scenario_coverage_metric_dict:
            scenario_coverage_metric_dict[coverage_metric_entity.type.value] = []
        scenario_coverage_metric_dict[coverage_metric_entity.type.value].append(get_coverage_value(coverage_metric_entity))

# print(f"from {coverage_info_target_id} to {last_id}")
# print(coverage_metric_dict)





output_dir = "coverage_graphs"
os.makedirs(output_dir, exist_ok=True)

saved_files = []

for metric_type in scenario_coverage_metric_dict:
    y_values_scenario = scenario_coverage_metric_dict.get(metric_type, [])
    y_values_random = random_coverage_metric_dict.get(metric_type, [])
    y_values_rule_random = rule_random_coverage_metric_dict.get(metric_type, [])

    max_len = max(len(y_values_rule_random), len(y_values_scenario))
    x_values = list(range(max_len))

    y_values_rule_random += [y_values_rule_random[-1]] * (max_len - len(y_values_rule_random))
    y_values_random += [y_values_random[-1]] * (max_len - len(y_values_random))
    y_values_scenario += [y_values_scenario[-1]] * (max_len - len(y_values_scenario))

    plt.figure(figsize=(5, 3))
    plt.plot(x_values, y_values_random, label="Random", linewidth=2)
    plt.plot(x_values, y_values_rule_random, label="Rule Random", linewidth=2)
    plt.plot(x_values, y_values_scenario, label="Scenario", linewidth=2)

    metric_name = "Coverage"
    match metric_type:
        case CoverageType.LINES.value:
            metric_name = "Line " + metric_name
        case CoverageType.STATEMENTS.value:
            metric_name = "Statement " + metric_name
        case CoverageType.FUNCTIONS.value:
            metric_name = "Function " + metric_name
        case CoverageType.BRANCHES.value:
            metric_name = "Branch " + metric_name
        case CoverageType.BRANCHES_TRUE.value:
            metric_name = "Branch True " + metric_name

    # plt.title(metric_name + " Comparison")
    plt.xlabel("Test Execution Count")
    plt.ylabel("Coverage (%)")
    plt.grid(True)
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()

    filename = f"re_{metric_type.lower()}_coverage_comparison.pdf"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, format="pdf", bbox_inches="tight")
    saved_files.append(filepath)
    print(filepath)
    plt.close()

for f in saved_files:
    print(f"- {f}")