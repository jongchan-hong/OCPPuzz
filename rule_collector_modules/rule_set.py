from pygments.lexers import q

from rule_collector_modules.constraint_define import ConstraintDefine, ConstraintEnum
from dto.constraint_collect_dto import Rule, Condition, Constraint


class RuleSet(set):
    ignore_constraint_case = [
        ConstraintEnum.OPTIONAL_EQUAL_TRUE,
        ConstraintEnum.REQUIRED_EQUAL_FALSE,
        ConstraintEnum.UNKNOWN_ATTRIBUTE,
        ConstraintEnum.MAX_LENGTH_EQUAL_MAX_LIMIT,
        ConstraintEnum.FORMAT_EQUAL_UTF8,
        ConstraintEnum.CHARACTER_SET_UTF8,
        ConstraintEnum.VALUE_IN_FALSE_AND_TRUE,
        ConstraintEnum.AGREED_UPON_BY_ALL_PARTIES,
        ConstraintEnum.CASE_INSENSITIVE,
        ConstraintEnum.CASE_SENSITIVE,
        ConstraintEnum.DEFAULT_EQUAL,
        ConstraintEnum.FORMAT_EQUAL_HUMAN_READABLE,
        ConstraintEnum.IMPLEMENTED_EQUAL_TRUE,
        ConstraintEnum.IMPLEMENTED_EQUAL_FALSE,
        ConstraintEnum.IMPLEMENTED_EQUAL_CUSTOM,
        ConstraintEnum.VALUE_MAX_DURATION_OF_THE_TRANSACTION,
        ConstraintEnum.VALUE_FROM_UNDEFINED,
        ConstraintEnum.RELEVANT_EQUAL,
        ConstraintEnum.UNTESTABLE_CONSTRAINT,
        ConstraintEnum.VALUE_MONITOR_VALUE,
        ConstraintEnum.VARIABLE_EQUAL_HEART_BEAT_INTERVAL,
        ConstraintEnum.MINIMUM_EQUAL_TRUE,
        ConstraintEnum.CERTIFICATE_TYPE_EQUAL,
        ConstraintEnum.MAX_ITEMS_EQUAL_MAX_SCHEDULE_TUPLES,
    ]
    def __init__(self, *args):
        super().__init__(*args)

    def add(self, item: Rule, force=False, rule_field_name = ""):
        if force:
            super().add(item)
            return True

        item = self.get_equivalent_rule(item)
        if item in self:
            existing_item = next(x for x in self if x == item)
            if set(existing_item.causes) == set(item.causes):
                return False
            item.causes.extend(existing_item.causes)
            existing_causes = [cause for cause in existing_item.causes if cause not in item.causes]
            self.remove(existing_item)
            item.causes.extend(existing_causes)
            super().add(item)
            return False
        else:
            super().add(item)
            return True

    def get_equivalent_rule(self, rule: Rule):
        constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)

        if constraint_enum == ConstraintEnum.VALUE_FROM and len(rule.constraint.values) > 1:
            rule.constraint = Constraint(
                attribute="value",
                operator="in",
                values=rule.constraint.values
            )
        if constraint_enum == ConstraintEnum.STATUS_EQUAL:
            rule.constraint = Constraint(
                attribute="values",
                operator="equal",
                values=rule.constraint.values
            )
        if constraint_enum == ConstraintEnum.TYPE_EQUAL and rule.constraint.values[0] == "dateTime":
            rule.constraint = Constraint(
                attribute="format",
                operator="equal",
                values=["date-time"]
            )
        if rule.constraint.attribute == "optional" and rule.constraint.operator == "equal" and rule.constraint.values[0] == "false":
            rule.constraint = Constraint(
                attribute="required",
                operator="equal",
                values=["true"]
            )
        if rule.constraint.attribute == "minimum" and rule.constraint.operator == "equal":
            rule.constraint = Constraint(
                attribute="values",
                operator="ge",
                values=rule.constraint.values
            )
        if rule.constraint.attribute == "variable" and rule.constraint.operator == "equal":
            if "variable.TariffCostCtrlr.Currency" in rule.constraint.values:
                rule.constraint = Constraint(
                    attribute="values",
                    operator="equal",
                    values=rule.constraint.values
                )
        if rule.conditions:
            for i in range(len(rule.conditions)):
                if (rule.conditions[i].attribute == "certificateTypeIncludedInSignCertificateRequest" and
                        rule.conditions[i].operator == "equal"
                ):
                    rule.conditions[i] = Condition(
                        attribute='certificateType',
                        target='context.SignCertificateRequest',
                        operator='provided',
                        values=rule.conditions[i].values
                    )
                if rule.conditions[i].attribute == "equal":
                    rule.conditions[i].attribute = "values"

                if rule.conditions[i].target == "context.centralContractValidation":
                    rule.conditions[i].target =  "variable.ISO15118Ctrlr.CentralContractValidationAllowed"
                if rule.conditions[i].target == "context.isFirstTransactionEventAfterEVConnection":
                    rule.conditions[i].attribute = "isFirstTransactionEventAfterEVConnection"
                    rule.conditions[i].target = "context"
        if rule.constraint.attribute == "values" and rule.constraint.operator == "equal":
            if len(rule.constraint.values) > 1:
                rule.constraint.operator = "in"
        if rule.constraint.operator == "custom":
            rule.constraint.operator = "equal"
        if rule.constraint.attribute =="values" and rule.constraint.operator == "required":
            rule.constraint.attribute = "required"
            rule.constraint.operator = "equal"
        if rule.constraint.attribute == "format" and rule.constraint.operator == "equal" and rule.constraint.values[0] == "base64":
            rule.constraint.attribute = "encoding"
        if rule.constraint.attribute == "minItems" and rule.constraint.operator == "ge":
            rule.constraint.operator = "equal"
        if rule.constraint.attribute == "format" and rule.constraint.operator == "equal" and rule.constraint.values[0] == "uri"  :
            rule.constraint.values[0] = "url"
        if rule.constraint.values and rule.constraint.values[0] == "decimal":
            rule.constraint.values[0] = "number"
        if rule.conditions == []:
            rule.conditions = None

        return rule