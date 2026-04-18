import sys
from enum import Enum
from typing import List
import math
from sqlalchemy import and_
import re
from generator_modules.fix_value_container import FixValueContainer
from parser_modules.parser import Parser
from generator_modules.payload_context import PayloadContext
from rule_collector_modules.rule_set import RuleSet
from constants.date_time_format import DateTimeFormat
from constants.format import Format
from generator_modules.value_config.generate_integer_value_config import GenerateIntegerValueConfig
from generator_modules.value_config.generate_number_value_config import GenerateNumberValueConfig
from constants.iso_version import ISO_version_list
from generator_modules.value_config.generate_string_value_config import GenerateStringValueConfig
from constants.variable_default_value import get_default_measurand
from rule_collector_modules.condition_define import ConditionDefine, ConditionEnum
from rule_collector_modules.constraint_define import ConstraintDefine, ConstraintEnum
from generator_modules.constraint.item_constraint import MinItemConstraint, MaxItemConstraint
from generator_modules.constraint.legnth_constraint import MinLengthConstraint, MaxLengthConstraint
from dto.constraint_collect_dto import Rule, Condition
from dto.prpert_value_generate_config import PropertyValueGenerateConfig
from storage.entity.generate_rule_combination_entity import GenerateRuleCombinationEntity
from storage.entity.generate_rule_combination_value_entity import GenerateRuleCombinationValueEntity
from storage.entity.request_id_log_entity import RequestIdLogEntity
import json
from exception.force_condition_exception import ForceConditionException
from exception.insufficient_data_exception import InsufficientDataException
from exception.uncreatable_value_exception import UncreatableValueException
from exception.wait_for_another_property_used_exception import WaitForAnotherPropertyUsedException
from generator_modules.format.RFC2986 import RFC2986
from generator_modules.format.RFC5646 import RFC5646
from generator_modules.format.der import DER
from generator_modules.format.html import HTML
from generator_modules.format.RFC3339 import RFC3339
from generator_modules.make_properties_seed_result import MakePropertiesSeedResult
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.x509 import Name, NameAttribute, CertificateBuilder, BasicConstraints
from cryptography.x509.oid import NameOID
import datetime
import random
import string
import base64
import binascii
from datetime import datetime, timedelta

from generator_modules.format.mac import MAC
from util.signature.signature import CITRINE_SIGNED_METHOD, CITRINE_ENCODING_METHOD, Signature


def chars_from_range(start, end):
    return [chr(i) for i in range(start, end + 1) if chr(i).isprintable()]

COMMON_UNICODE_PRINTABLES = (
    list(string.printable)
    + chars_from_range(0x00A0, 0x024F)  # Latin extended
    + chars_from_range(0xAC00, 0xD7A3)  # Hangul
    + chars_from_range(0x3040, 0x309F)  # Hiragana
    + chars_from_range(0x30A0, 0x30FF)  # Katakana
    + chars_from_range(0x4E00, 0x4E80)  # CJK
    + chars_from_range(0x1F600, 0x1F64F)  # Emojis
)
def rule_serializer(obj):
    if isinstance(obj, RuleSet):
        return list(obj)
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)

class PayloadGenerator(object):
    STAND_BY = "STAND_BY"
    EMPTY_VALUE = "EMPTY_VALUE"
    GEN_CNT = 1
    DEFAULT_MIN_LENGTH = 0
    DEFAULT_MAX_LENGTH = 12000
    DEFAULT_MIN_SIZE = 0
    DEFAULT_MAX_SIZE = 10
    MAX_SIZE_APPEND = 5
    INTEGER_MIN_SIZE = -sys.maxsize - 1
    INTEGER_MAX_SIZE = sys.maxsize

    def __init__(self, message_name:str,
                 rules:List[Rule],
                 generate_rule_combination_entity:GenerateRuleCombinationEntity,
                 fix_value_container:FixValueContainer,
                 parser:Parser,
                 test_controller_manager,
                 session
                 ):
        self.session = session
        self.message_name = message_name
        self.rules = rules
        self.generate_rule_combination_entity = generate_rule_combination_entity
        self.determine_generate_rule_combination_value = self.get_determine_generate_rule_combination_value()
        self.determine_rule = self.get_determine_rule(self.determine_generate_rule_combination_value)
        self.fix_value_container = fix_value_container
        self.test_controller_manager = test_controller_manager
        self.parser = parser
        self.signature_dict = {}
        self.used_token_set = set()
        self.determine_hit = False


        print("******************determine_rule***************** START")
        print(self.determine_rule)
        print("******************determine_rule***************** END")

    def get_determine_rule(self, determine_generate_rule_combination_value:GenerateRuleCombinationValueEntity):
        if determine_generate_rule_combination_value:
            return determine_generate_rule_combination_value.generate_rule_entity.to_dto()
        return None

    def get_determine_generate_rule_combination_value(self):
        return self.session.query(GenerateRuleCombinationValueEntity).filter(
            and_(
                GenerateRuleCombinationValueEntity.is_active == False,
                GenerateRuleCombinationValueEntity.generate_rule_combination_entity == self.generate_rule_combination_entity,
            )
        ).first()

    def is_determine_rule(self, rule):
        result = False
        if self.determine_generate_rule_combination_value:
            result = self.determine_generate_rule_combination_value.generate_rule_id == rule._generate_rule_entity.id
        return result


    def create(self, context:PayloadContext = None):
        self.context = context
        seed = self.make_seed(self.message_name, self.rules)
        if self.context.force_event_type:
            seed["eventType"] = self.context.force_event_type
        if self.context.force_trigger_reason:
            seed["triggerReason"] =self.context.force_trigger_reason

        result = self.clean_json(seed)
        if self.determine_rule and not self.determine_hit:
            raise UncreatableValueException(f"determine rule was not affected {self.determine_generate_rule_combination_value.generate_rule_id}")
        return  result

    def print_generate_rule_entity_ids(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "rules":
                    for rule in value:
                        if hasattr(rule, "_generate_rule_entity") and hasattr(rule._generate_rule_entity, "id"):
                            print(rule._generate_rule_entity.id)
                        else:
                            print("No _generate_rule_entity or id in rule:", rule)
                else:
                    self.print_generate_rule_entity_ids(value)
        elif isinstance(data, list):
            for item in data:
                self.print_generate_rule_entity_ids(item)

    def print_any_rule_info(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "rules":
                    print("rules type:", type(value))
                    for rule in value:
                        print("rule type:", type(rule), "rule repr:", repr(rule))
                else:
                    self.print_any_rule_info(value)
        elif isinstance(data, list):
            for item in data:
                self.print_any_rule_info(item)

    @staticmethod
    def clean_json( result):
        result = json.dumps(result, ensure_ascii=False, default=rule_serializer)
        result = re.sub(r'[\x00-\x1F\x7F]', '', result)
        cleaned_json = json.loads(result)
        cleaned_json = json.dumps(cleaned_json, ensure_ascii=False)
        return cleaned_json

    def get_combination_value_entity(self, rule):
        rule_set = RuleSet()
        return next(
            (
                grcve for grcve in self.generate_rule_combination_entity.generate_rule_combination_value_entity_list
                if grcve.generate_rule_entity.object_name ==  rule._generate_rule_entity.object_name and
                   grcve.generate_rule_entity.field_name == rule._generate_rule_entity.field_name and
                   rule_set.get_equivalent_rule(rule = grcve.generate_rule_entity.to_dto()) == rule_set.get_equivalent_rule(rule = rule._generate_rule_entity.to_dto())
            ),
            None
        )
    def generate_random_x509_pem_cert(self, length):
        class Mode(Enum):
            Normal = 1
            BIG = 2
        mode = Mode.Normal

        if length > 5500:
            mode = Mode.BIG

        key_size = 2048 if mode == Mode.Normal else 8192

        def random_string(length=10):
            return ''.join(random.choices(string.ascii_letters, k=length))
        country = random_string(2)
        state = random_string(8 if mode == Mode.Normal else 1000)
        city = random_string(6 if mode == Mode.Normal else 1000)
        organization = random_string(12 if mode == Mode.Normal else 1000)
        common_name = f"{random_string(6 if mode == Mode.Normal else 60)}.com"

        days_valid = 365

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )

        public_key = private_key.public_key()

        subject = issuer = Name([
            NameAttribute(NameOID.COUNTRY_NAME, country),
            NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            NameAttribute(NameOID.LOCALITY_NAME, city),
            NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        cert = CertificateBuilder() \
            .subject_name(subject) \
            .issuer_name(issuer) \
            .public_key(public_key) \
            .serial_number(1001) \
            .not_valid_before(datetime.now()) \
            .not_valid_after(datetime.now() + timedelta(days=days_valid)) \
            .add_extension(BasicConstraints(ca=True, path_length=None), critical=True) \
            .sign(private_key, hashes.SHA256())

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        cert_pem = cert.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode()
        return cert_pem

    def generate_random_url(self, length: int):
        schemes_web = ("http", "https", "ftp")
        schemes = ["http", "https", "ftp", "file"]

        length = max(10, length)
        scheme = random.choice(schemes)

        def build_file(prefix_len: int) -> str:
            remaining = length - prefix_len
            if remaining <= 0:
                return "/"
            body = "/" + "".join(
                random.choices(string.ascii_lowercase + string.digits + "/._-", k=remaining - 1)
            )
            return body

        def build_web(prefix_len: int) -> str:
            remaining = length - prefix_len
            if remaining < 5:
                return None
            tlds = [".com", ".net", ".org", ".io"]
            tld = next((t for t in sorted(tlds, key=len) if remaining - len(t) >= 1), ".com")
            host_label_len = remaining - len(tld)
            host_label = "".join(random.choices(string.ascii_lowercase + string.digits + "-", k=host_label_len))
            return host_label + tld

        prefix = f"{scheme}://"

        if scheme in schemes_web:
            body = build_web(len(prefix))
            if body is None:
                scheme = "file"
                prefix = f"{scheme}://"
                body = build_file(len(prefix))
        else:
            body = build_file(len(prefix))

        url = prefix + body
        if len(url) != length:
            if len(url) < length:
                pad_len = length - len(url)
                pad_chars = string.ascii_lowercase + string.digits + "-._~:/?#[]@!$&'()*+,;=%"
                url += "".join(random.choices(pad_chars, k=pad_len))
            else:
                url = url[:length]
        return url

    def generate_random_datetime(self):
        start_date = "2000-01-01"
        end_date = "2030-12-31"

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        random_days = random.randint(0, (end_dt - start_dt).days)
        random_dt = start_dt + timedelta(
            days=random_days,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        datetime_formats = [
            "%Y-%m-%d",  # 2025-03-18
            "%m/%d/%Y",  # 03/18/2025
            "%d-%b-%Y",  # 18-Mar-2025
            "%A, %d %B %Y",  # Tuesday, 18 March 2025
            "%I:%M %p %d-%m-%Y",  # 02:30 PM 18-03-2025
            "%s",
        ]

        format_type = random.choice(datetime_formats)

        if format_type == "%s":
            return str(int(random_dt.timestamp()))

        return random_dt.strftime(format_type)

    def generate_random_string_value(self, config:GenerateStringValueConfig):
        if config.is_random_empty_value_status() == True:
            return PayloadGenerator.EMPTY_VALUE

        if config.is_determine_property == False:
            if config.empty_string:
                return ""
            if config.remove:
                return PayloadGenerator.EMPTY_VALUE
            if config.signature:
                if config.base64_encoding:
                    return config.signature.get_public_key()
                else:
                    return config.signature.get_public_key(base64_encode=False)

        equal_value = config.get_equal_value()
        if equal_value:
            return equal_value

        if config.is_enum_string():
            enum_result = config.get_random_enum_value()
            if enum_result:
                return enum_result
        length = config.get_generate_value_random_length()
        result = None
        prefix = None
        if config.not_allowed_characters:
            config.population_constraint.set(
                value= self.generate_limit_charset_random_string(config.not_allowed_characters,config.population_constraint.value),
                level=9999
            )

        if config.allow_prefix_set:
            prefix = random.choice(list(config.allow_prefix_set))
            length = length - len(prefix)
            if config.required_characters:
                for character in config.required_characters:
                    length = length - len(character)
        if config.format_constraint:
            match config.format_constraint.value:
                case Format.URL:
                    result = self.generate_random_url(length-10)
                case Format.PEM:
                    result = self.generate_random_x509_pem_cert(length * 0.8)
                case Format.NUMBER:
                    number_string = "".join(random.choices(string.digits, k=length))
                    if number_string:
                        return int(number_string)
                    return 0
                case Format.DATE_TIME:
                    if config.date_time_format == DateTimeFormat.RFC3339:
                        result = RFC3339.random_generate(config.max_decimal_places)
                    else:
                        result = self.generate_random_datetime()
                case Format.RFC5646:
                    result = RFC5646.generate_random_language_tag_value(
                        min_length=config.min_length_constraint.length if config.min_length_constraint else 0,
                        max_length=config.max_length_constraint.length if config.max_length_constraint else self.DEFAULT_MAX_LENGTH,
                    )
                case Format.RFC2986:
                    result = RFC2986.generate_random_value(length)
                case Format.HTML:
                    result = HTML.generate_fixed_length_html(length)
                case Format.DER:
                    result = DER.generate_fixed_length(length)
                case Format.MAC:
                    result = MAC.generate_random_value()
                    if config.min_length_constraint and config.min_length_constraint.length > len(result):
                        result = "".join(random.choices(config.population_constraint.value, k=(length)))
                case Format.NOTHING:
                    result = "".join(random.choices(config.population_constraint.value, k=(length)))
                case _:
                    print(f"unknown format in generate_random_value {config.format_constraint.value}")
        else:
            result = "".join(random.choices(config.population_constraint.value, k=(length)))



        if config.required_characters:
            for character in config.required_characters:
                result = self.insert_at_random_position(result, character)


        if config.not_allow_prefix_set:
            for not_allow_prefix in config.not_allow_prefix_set:
                while result.startswith(not_allow_prefix):
                    result = result[len(not_allow_prefix):]
        if prefix:
            result = prefix + result

        if config.base64_encoding == True:
            if result is not None:
                input_bytes = None
                if isinstance(result, str):
                    input_bytes = result.encode('utf-8')
                elif isinstance(result, bytes):
                    input_bytes = result
                encoded = base64.b64encode(input_bytes).decode()
                if config.min_length_constraint:
                    min_length = config.min_length_constraint.length
                    encoded = self.get_base64_with_min_length(min_length)
                else:
                    while len(encoded) > length:
                        ratio = length / len(encoded) * 0.99
                        new_len = int(len(input_bytes) * ratio)
                        if new_len <= 0:
                            encoded = ""
                            break
                        input_bytes = input_bytes[:new_len]
                        encoded = base64.b64encode(input_bytes).decode()
                result = encoded
            else:
                raw_data = "".join(random.choices(config.population_constraint.value, k=length)).encode()
                result = base64.b64encode(raw_data).decode()

        return result

    def get_base64_with_min_length(self, min_length):
        population = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        target_base64_length = math.ceil(min_length / 4) * 4
        raw_data_length = math.ceil(target_base64_length / 4 * 3)
        raw_data = "".join(random.choices(population, k=raw_data_length)).encode()
        encoded = base64.b64encode(raw_data).decode()
        return encoded

    def create_simple_value_with_except_type(self, except_type_list:List[str] = None):
        list = ["string", "number", "integer", "null", "boolean", "array", "object"]
        if except_type_list:
            for except_type in except_type_list:
                if except_type in list:
                    list.remove(except_type)
        type = random.choice(list)
        match type:
            case "string":
                return "".join(random.choices(string.printable, k=5))
            case "number":
                return random.uniform(PayloadGenerator.INTEGER_MIN_SIZE, PayloadGenerator.INTEGER_MAX_SIZE)
            case "integer":
                return random.randint(PayloadGenerator.INTEGER_MIN_SIZE, PayloadGenerator.INTEGER_MAX_SIZE)
            case "boolean":
                return random.choice([True, False])
            case "array":
                return [self.create_simple_value_with_except_type(["array"])]
            case "object":
                return {
                    "key": self.create_simple_value_with_except_type(["object"])
                }
            case "null":
                return None

    def generate_integer_value(self, property_value_generate_config:PropertyValueGenerateConfig):
        config = GenerateIntegerValueConfig()
        for rule in property_value_generate_config.property_value["rules"]:
            is_active: bool = self.is_active_rule(rule, property_value_generate_config)
            if is_active == False:
                config.is_determine_property = True

            if rule.conditions is not None:
                if self.check_condition_hit(rule, is_active, property_value_generate_config) == False:
                    continue
            constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
            match constraint_enum:
                case ConstraintEnum.TYPE_EQUAL:
                    if rule.constraint.values[0] == "integer":
                        if is_active == False:
                            return self.create_simple_value_with_except_type(["integer"])
                case ConstraintEnum.WAS_PROVIDED_IN:
                    if is_active:
                        provided_in_id = self.context.get_provided_in_id(rule.constraint.values[0])

                        if not provided_in_id:
                            if rule.constraint.values[0] == "RequestStartTransactionRequest":
                                config.enum_integer_list.append(PayloadGenerator.EMPTY_VALUE)
                            else:
                                config.stand_by_raise_exception = InsufficientDataException(f"Not trigger request id")
                        else:
                            config.enum_integer_list.append(int(provided_in_id))
                    else:
                        request_id_log_entity = self.session.query(RequestIdLogEntity) \
                            .order_by(RequestIdLogEntity.id.desc()) \
                            .first()
                        start_id = request_id_log_entity.id if request_id_log_entity else 0
                        config.min_size_constraint.set(start_id + 1000000, True)
                        config.max_size_constraint.set(start_id + 1000200, True)
                case ConstraintEnum.REQUIRED_EQUAL_TRUE:
                    if is_active == False:
                        return PayloadGenerator.EMPTY_VALUE
                    else:
                        config.required = True
                case ConstraintEnum.VALUE_GE:
                    if is_active:
                        config.min_size_constraint.set(int(rule.constraint.values[0]))
                    else:
                        config.max_size_constraint.set(int(rule.constraint.values[0]) - 1, True)
                case ConstraintEnum.NOT_LEADING_ZEROS:
                    if is_active == False:
                        raise UncreatableValueException("reverse [not leading zero] value is uncreatable value")
                case ConstraintEnum.BIT_EQUAL:
                    bit = int(rule.constraint.values[0])
                    if is_active:
                        config.min_size_constraint.set(-(1 << (bit-1)))
                        config.max_size_constraint.set((1 << (bit-1)) - 1)
                    else:
                        if random.choice([True, False]):
                            config.min_size_constraint.set((1 << (bit-1)), True)
                            config.max_size_constraint.set((1 << (bit-1)) * 10, True)
                        else:
                            config.min_size_constraint.set(-(1 << (bit-1)) * 10, True)
                            config.max_size_constraint.set(-(1 << (bit-1)) -1, True)
                case ConstraintEnum.PREFIX_NOT_EQUAL:
                    value = rule.constraint.values[0]
                    if value == "+":
                        if is_active == False:
                            raise UncreatableValueException("prefix [+] integer value is uncreatable value")
                case ConstraintEnum.VALUE_BETWEEN:
                    start = int(rule.constraint.values[0])
                    end = int(rule.constraint.values[1])
                    if is_active == True:
                        config.min_size_constraint.set(start)
                        config.max_size_constraint.set(end)
                    else:
                        config.except_integer_list.extend(range(start, end + 1))
                case ConstraintEnum.REMOVE_FIELD_EQUAL_TRUE:
                    if is_active == True:
                        config.enum_integer_list.append(PayloadGenerator.EMPTY_VALUE)
                    else:
                        config.required = True
                case ConstraintEnum.VALUE_GT:
                    if is_active == True:
                        config.min_size_constraint.set(int(rule.constraint.values[0]) + 1)
                    else:
                        config.max_size_constraint.set(int(rule.constraint.values[0]), True)
                        config.min_size_constraint.set(int(rule.constraint.values[0]) - 100, True)

                case ConstraintEnum.VALUE_NOT_EQUAL:
                    if is_active == True:
                        for value in rule.constraint.values:
                            config.except_integer_list.append(value)
                    else:
                        return int(random.choice(rule.constraint.values))
                case ConstraintEnum.MAXIMUM_EQUAL:
                    value = int(rule.constraint.values[0])
                    if is_active == True:
                        config.max_size_constraint.set(value)
                    else:
                        config.min_size_constraint.set(value + 1, True)
                        config.max_size_constraint.set(value + 500, True)
                case ConstraintEnum.ONCE_PER_TRANSACTION_EQUAL_TRUE:
                    match property_value_generate_config.property_key:
                        case "reservationId":
                            if is_active == True:
                                if self.context:
                                    if not self.context.is_first_transaction_event_with_reservation_id():
                                        config.enum_integer_list.append(PayloadGenerator.EMPTY_VALUE)
                            else:
                                if not self.context:
                                    raise UncreatableValueException("[ONCE_PER_TRANSACTION_EQUAL_TRUE] not self.context")

                                if self.context.is_first_transaction_event_with_reservation_id():
                                    raise UncreatableValueException("[ONCE_PER_TRANSACTION_EQUAL_TRUE] not have a reservation_id")
                                else:
                                    config.required = True
                case _:
                    if is_active == False:
                        raise UncreatableValueException("unknown constraint in generate_integer_value")

        if self.context.required_reservation_id_constraint and property_value_generate_config.property_key == "reservationId":
            config.required = True
        if config.stand_by_raise_exception:
            raise config.stand_by_raise_exception

        if config.is_random_empty_value_status() == True:
            return PayloadGenerator.EMPTY_VALUE

        if len(config.enum_integer_list) > 0:
            if config.is_determine_property == False and PayloadGenerator.EMPTY_VALUE in config.enum_integer_list:
                return PayloadGenerator.EMPTY_VALUE
            min_size = config.min_size_constraint.size
            max_size = config.max_size_constraint.size
            filtered = [
                value for value in config.enum_integer_list
                if value != PayloadGenerator.EMPTY_VALUE and
                   (min_size is None or min_size <= value) and
                   (max_size is None or value <= max_size)
            ]
            if filtered:
                return random.choice(filtered)
        while True:
            result = random.randint(config.min_size_constraint.size, config.max_size_constraint.size)
            if result not in config.except_integer_list:
                return result

    def generate_random_decimal(self, config:GenerateNumberValueConfig):
        integer_part = random.randint(PayloadGenerator.INTEGER_MIN_SIZE, PayloadGenerator.INTEGER_MAX_SIZE)
        fractional_part = random.randint(0, 10 ** config.max_decimal_places - 1)
        return float(f"{integer_part}.{fractional_part:0{config.max_decimal_places}d}")

    def generate_boolean_value(self, property_value_generate_config:PropertyValueGenerateConfig):
        required = False
        if property_value_generate_config.property_value["rules"]:
            for rule in property_value_generate_config.property_value["rules"]:
                is_active: bool = self.is_active_rule(rule, property_value_generate_config)
                if rule.conditions is not None:
                    if self.check_condition_hit(rule, is_active, property_value_generate_config) == False:
                        continue
                constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
                match constraint_enum:
                    case ConstraintEnum.TYPE_EQUAL:
                        value = rule.constraint.values[0]
                        match value:
                            case "boolean":
                                if is_active == False:
                                    return self.create_simple_value_with_except_type(["boolean"])
                    case ConstraintEnum.REQUIRED_EQUAL_TRUE:
                        if is_active == False:
                            return PayloadGenerator.EMPTY_VALUE
                        required = True
                    case ConstraintEnum.VALUE_IN_FALSE_AND_TRUE:
                        if is_active == False:
                            return self.create_simple_value_with_except_type(["boolean"])
                    case ConstraintEnum.VALUE_EQUAL:
                        if is_active:
                            choice = random.choice(rule.constraint.values)
                            if choice == "false":
                                return False
                            elif choice == "true":
                                return True
                        else:
                            return self.create_simple_value_with_except_type(["boolean"])
                    case _:
                        if is_active == False:
                            raise UncreatableValueException("unknown constraint in generate_boolean_value")
        if not required and random.choice([True, False]):
            return PayloadGenerator.EMPTY_VALUE
        return random.choice([True, False])

    def generate_number_value(self, property_value_generate_config:PropertyValueGenerateConfig):
        config = GenerateNumberValueConfig()
        if property_value_generate_config.property_value["rules"]:
            for rule in property_value_generate_config.property_value["rules"]:
                is_active: bool = self.is_active_rule(rule, property_value_generate_config)
                if not is_active:
                    config.is_determine_property = True
                if rule.conditions is not None:
                    if not self.check_condition_hit(rule, is_active, property_value_generate_config):
                        continue
                constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
                match constraint_enum:
                    case ConstraintEnum.DECIMAL_PLACES_MAX:
                        max_decimal_places = int(rule.constraint.values[0])
                        if is_active:
                            config.max_decimal_places = max_decimal_places
                        else:
                            config.max_decimal_places = max_decimal_places + random.randint(1, 20)
                    case ConstraintEnum.TYPE_EQUAL:
                        value = rule.constraint.values[0]
                        match value:
                            case "number":
                                if is_active == False:
                                    return self.create_simple_value_with_except_type(["number", "integer"])
                            case _:
                                print(f"unknown TYPE_EQUAL value in generate_number_value {value}")
                                continue
                    case ConstraintEnum.REQUIRED_EQUAL_TRUE:
                        if is_active:
                            config.required = True
                        else:
                            return PayloadGenerator.EMPTY_VALUE
                    case _:
                        if is_active == False:
                            raise UncreatableValueException("unknown constraint in generate_number_value")
        if config.is_random_empty_value_status():
            return PayloadGenerator.EMPTY_VALUE
        return self.generate_random_decimal(config)

    def is_variable_name(self, name):
        for variable in self.parser.referenced_components_and_variables_parser.variable_list:
            if name == variable.get_variable_name():
                return True

    def check_condition_hit(self, rule, is_active, property_value_generate_config:PropertyValueGenerateConfig)-> bool:
        result = True
        force_condition_list = []
        for condition in rule.conditions:
            target_value = ""
            target_type = None
            name = None
            if condition.target:
                condition_target_arr = condition.target.split(".")
                target_type = condition_target_arr[0]
                name = condition_target_arr[-1]
                match target_type:
                    case "fixValueContainer":
                        target_value = self.fix_value_container.get_value(parent_key= condition_target_arr[1], field_name = condition_target_arr[2])
                    case "variable":
                        component_name = condition_target_arr[-2]
                        variable_name = condition_target_arr[-1]
                        target_value = self.context.get_variable_value(component_name, variable_name)
                    case "context":
                        target_value = None
                        match name:
                            case "eventType":
                                target_value = self.context.event_type
                            case "triggerReason":
                                target_value = self.context.get_trigger_reason(condition.values)
                            case "hasSentPublicKeyBefore":
                                target_value = self.context.has_sent_public_key_before()
                            case "triggeredBy":
                                if "TriggerMessageRequest" in condition.values:
                                    if self.context.is_trigger_by_trigger_message_request():
                                        target_value = "TriggerMessageRequest"
                            case "stoppedBy":
                                 target_value = self.context.get_stopped_by_message()
                            case "firmwareUpdateOngoing":
                                if self.context.firmware_update_ongoing():
                                    target_value = "true"
                                else:
                                    target_value = "false"
                            case "isFirstTransaction":
                                if self.context.is_first_transaction():
                                    target_value = "true"
                                else:
                                    target_value = "false"
                            case "isFirstTransactionEventAfterAuthorization":
                                if self.context.is_first_transaction_event_after_authorization():
                                    target_value = "true"
                                else:
                                    target_value = "false"
                    case "field"|_:
                        target_value = property_value_generate_config.result.get(name)
                        if self.is_not_in_parent_field(name, property_value_generate_config):
                            if not is_active:
                                raise UncreatableValueException(f"condition field {name} is not in parent object")
                            result = False
                            continue
                        if name not in property_value_generate_config.used_property_key_set:
                            raise WaitForAnotherPropertyUsedException(f"{name} need to used")

            match ConditionDefine.getConditionEnum(condition):
                case ConditionEnum.CERTIFICATE_TYPE_PROVIDED_IN_SIGN_REQUEST:
                    provided_in_sign_request = self.context.certificate_type_provided_in_sign_request()
                    if (condition.values[0] == "true" and not provided_in_sign_request) or (condition.values[0] == "false" and provided_in_sign_request):
                        result = False
                        if not is_active:
                            raise UncreatableValueException(f"[CERTIFICATE_TYPE_PROVIDED_IN_SIGN_REQUEST] can't force")

                case ConditionEnum.STOPPED_BY_REQUEST_STOP_TRANSACTION_REQUEST:
                    if not self.context.is_stopped_by_request_stop_transaction_request():
                        result = False
                        if not is_active:
                            raise UncreatableValueException(f"[STOPPED_BY_REQUEST_STOP_TRANSACTION_REQUEST] can't force")
                case ConditionEnum.IS_FIRST_TRANSACTION_EVENT_AFTER_AUTHORIZATION_EQUAL_FALSE:
                    if not self.context:
                        result = False
                    if self.context.is_first_transaction_event_after_authorization():
                        if not is_active:
                            raise UncreatableValueException("can't force IS_FIRST_TRANSACTION_EVENT_AFTER_AUTHORIZATION_EQUAL_FALSE")
                        result = False
                case ConditionEnum.IS_FIRST_TRANSACTION_EVENT_AFTER_EV_CONNECTION_EQUAL_FALSE:
                    trigger_reason = property_value_generate_config.result.get("triggerReason")
                    if self.context and self.context.is_first_transaction_event_after_ev_connection_equal_true(trigger_reason):
                        if not is_active:
                            if trigger_reason not in self.context.ev_connection_trigger_reason_list:
                                self.context.set_force_trigger_reason(random.choice(self.context.ev_connection_trigger_reason_list))
                        else:
                            result = False
                case ConditionEnum.EXIST_EQUAL_FALSE:
                    if target_value:
                        if not is_active:
                            if target_type == "fixValueContainer":
                                raise UncreatableValueException(f"[EXIST_EQUAL_FALSE] can't force value")
                        result = False
                case ConditionEnum.TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST:
                    if not self.context.is_trigger_by_trigger_message_request():
                        result = False
                        if not is_active:

                            raise UncreatableValueException(f"can't force TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST")
                case ConditionEnum.NOT_TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST:
                    if self.context.is_trigger_by_trigger_message_request():
                        result = False
                        if not is_active:
                            raise UncreatableValueException(f"can't force NOT_TRIGGERED_BY_TRIGGER_MESSAGE_REQUEST")
                case ConditionEnum.VALUE_IN:
                    if target_value not in condition.values:
                        if not is_active:
                            if target_type == "variable":
                                raise UncreatableValueException(f"VALUE_IN: variable:{name} /value:{target_value}")
                            elif target_type == "context":
                                raise UncreatableValueException(f"VALUE_IN: context:{name} /value:{target_value}")
                            else:
                                force_condition_list.append(condition)
                        result = False
                case ConditionEnum.VALUE_EQUAL:
                    if not target_value or condition.values[0] != target_value:
                        if not is_active:
                            print(f"check_condition_hit is not active {condition.values[0]} {target_value}")
                            if target_type == "variable":
                                raise UncreatableValueException(f"VALUE_EQUAL: variable:{name} /value:{target_value} : {condition.values[0]}")
                            elif target_type == "context":
                                if name == "eventType":
                                    self.context.set_force_event_type(condition.values[0])
                                if name == "triggerReason":
                                    self.context.set_force_trigger_reason(condition.values[0])
                                else:
                                    raise UncreatableValueException(f"VALUE_EQUAL: context:{name} /value:{target_value} : {condition.values[0]}")
                            else:
                                result = False
                                print("check_condition_hit is not active")
                                force_condition_list.append(condition)
                        else :
                            result = False
                case ConditionEnum.VALUE_NOT_EQUAL:
                    if str(condition.values[0]) == str(target_value):
                        if not is_active:
                            if target_type == "variable":
                                raise UncreatableValueException(f"VALUE_NOT_EQUAL: variable:{name} /value:{target_value}")
                            if name != "eventType" or not self.fix_value_container.get_value("TransactionEventRequest","eventType"):
                                force_condition_list.append(condition)
                        result = False
                case ConditionEnum.MESSAGE_TYPE_NOT_EQUAL:
                    if self.message_name == condition.values[0]:
                        if not is_active:
                            raise UncreatableValueException(f"MESSAGE_TYPE_NOT_EQUAL: Can't modify message to  {condition.values[0]}")
                        result = False
                case ConditionEnum.PROVIDED_EQUAL_FALSE:
                    if target_value:
                        if not is_active:
                            if target_type == "variable":
                                raise UncreatableValueException(f"PROVIDED_EQUAL_FALSE: variable:{name} /value:{target_value}")
                            force_condition_list.append(condition)
                        result = False
                case ConditionEnum.MESSAGE_TYPE_EQUAL:
                    if self.message_name != condition.values[0]:
                        if not is_active:
                            raise UncreatableValueException(f"MESSAGE_TYPE_EQUAL: Can't modify message to  {condition.values[0]}")
                        result = False
                case _:
                    print("unknown condition match")
                    print(rule)
                    continue
        if force_condition_list:
            raise ForceConditionException(
                message="force condition list is not empty",
                force_condition_list = force_condition_list
            )
        return result

    def is_not_in_parent_field(self, field_name, property_value_generate_config):
        return field_name not in property_value_generate_config.parent_value and field_name not in property_value_generate_config.used_property_key_set

    def expand_charset(self, charset):
        result = []
        for item in charset:
            if item == 'a-z':
                result.extend(string.ascii_lowercase)
            elif item == 'A-Z':
                result.extend(string.ascii_uppercase)
            elif item == '0-9':
                result.extend(string.digits)
            else:
                result.append(item)
        return result

    def generate_limit_charset_random_string(self, charset, all_chars=None):
        expanded_chars = self.expand_charset(charset)

        if all_chars is not None:
            expanded_chars = [c for c in all_chars if c not in expanded_chars]
        return expanded_chars

    def generate_string_value(self, property_value_generate_config:PropertyValueGenerateConfig):
        config = GenerateStringValueConfig(COMMON_UNICODE_PRINTABLES)

        if property_value_generate_config.property_key == "measurand":
            if property_value_generate_config.force_measurand:
                return property_value_generate_config.force_measurand

            if property_value_generate_config.force_not_in_measurand_set:
                for measurand in property_value_generate_config.force_not_in_measurand_set:
                    config.except_string_list.append(measurand)

        for rule in property_value_generate_config.property_value["rules"]:
            is_active:bool = self.is_active_rule(rule, property_value_generate_config)
            if not is_active:
                config.is_determine_property = True
            if rule.conditions is not None:
                if self.check_condition_hit(rule, is_active, property_value_generate_config) == False:
                    continue


            match ConstraintDefine.getConstraintEnum(rule.constraint):
                case ConstraintEnum.MAX_LENGTH | ConstraintEnum.MAXIMUM_EQUAL:
                    value = None
                    try:
                        value = int(rule.constraint.values[0])
                    except ValueError:
                        value_split_list = rule.constraint.values[0].split(".")
                        if value_split_list[0] == "variable":
                            value = self.context.get_variable_value(value_split_list[-2], value_split_list[-1])
                            if value is None:
                                if not is_active:
                                    raise UncreatableValueException(f"ConstraintEnum.MAX_LENGTH: variable:{value_split_list[-1]}")
                            else:
                                value = int(value)
                        if value is None:
                            continue
                    except Exception as e:
                        print("e1")

                    if is_active:
                        max_length_value = value
                        config.max_length_constraint = MaxLengthConstraint.update(
                            constraint=config.max_length_constraint,
                            length=max_length_value,
                            force=False
                        )
                    else:
                        config.active_enum = False
                        min_length_value = value + 1
                        config.min_length_constraint = MinLengthConstraint.update(
                            constraint=config.min_length_constraint,
                            length=min_length_value,
                            force=True
                        )
                        config.max_length_constraint = MaxLengthConstraint.update(
                            constraint=config.max_length_constraint,
                            length=min_length_value + 100,
                            force=True
                        )
                case ConstraintEnum.BYTES_FIX:
                    if is_active:
                        byte_length = int(random.choice(rule.constraint.values))
                        config.max_length_constraint = MaxLengthConstraint.update(
                            constraint=config.max_length_constraint,
                            length=byte_length,
                            force=False
                        )
                        config.min_length_constraint = MinLengthConstraint.update(
                            constraint=config.min_length_constraint,
                            length=byte_length,
                            force=False
                        )
                    else:
                        config.byte_fix_excluded_lengths = set(map(int, rule.constraint.values))

                case ConstraintEnum.ENUM:
                    for value in rule.constraint.values:
                        if is_active:
                            config.enum_list.append(value)
                        else:
                            config.except_string_list.append(value)
                case ConstraintEnum.TYPE_EQUAL:
                    type = rule.constraint.values[0]
                    if not is_active:
                        config.active_enum = False
                    match type:
                        case "string":
                            if is_active == False:
                                return self.create_simple_value_with_except_type(["string"])
                        case _:
                            print("unknown type match in generate_string_value type equal")
                            print(rule)
                            continue
                case ConstraintEnum.REQUIRED_EQUAL_TRUE:
                    if not is_active:
                        return PayloadGenerator.EMPTY_VALUE
                    else:
                        config.required = True
                case ConstraintEnum.FORMAT_EQUAL_HEX:
                    if not is_active:
                        config.population_constraint.set(
                            value=''.join(set(string.printable) - set(string.hexdigits.lower())),
                            level = 999
                        )
                    else:
                        config.population_constraint.set(
                            value=string.hexdigits.lower(),
                            level = 3
                        )
                case ConstraintEnum.JAVA_TYPE_EQUAL:
                    if is_active == False:
                        config.set_format_constraint(Format.NUMBER, True)
                        if rule.constraint.values[0].endswith("EnumType") or rule.constraint.values[0].endswith("Enum"):
                            config.active_enum = False
                case ConstraintEnum.FORMAT_EQUAL:
                    format_value = rule.constraint.values[0].lower().replace(" ", "")
                    match format_value:
                        case "url" | "uri":
                            if is_active != False:
                                config.set_format_constraint(Format.URL)
                        case "rfc3339":
                            if is_active != False:
                                config.date_time_format = DateTimeFormat.RFC3339
                        case "date-time":
                            if is_active != False:
                                config.set_format_constraint(Format.DATE_TIME)
                        case "rfc5646":
                            if is_active != False:
                                config.set_format_constraint(Format.RFC5646)
                        case "html":
                            if is_active != False:
                                config.set_format_constraint(Format.HTML)
                                config.min_length_constraint = MinLengthConstraint.update(
                                    constraint=config.min_length_constraint,
                                    length=HTML.MIN_LENGTH_LIMIT,
                                    force=False
                                )
                        case "mac":
                            if is_active != False:
                                config.set_format_constraint(Format.MAC)
                        case "ascii":
                            population = string.printable.strip()
                            if is_active == True:
                                config.population_constraint.set(
                                    value = population,
                                    level = 3
                                )
                            else:
                                result = self.expand_charset(population)
                                config.not_allowed_characters.extend(result)
                                config.population_constraint.set(
                                    value=self.generate_limit_charset_random_string(population, COMMON_UNICODE_PRINTABLES),
                                    level=999
                                )
                        case "rfc2986":
                            if is_active != False:
                                config.set_format_constraint(Format.RFC2986)
                            else:
                                config.set_format_constraint(Format.NOTHING, True)
                        case "der":
                            if is_active != False:
                                config.set_format_constraint(Format.DER)
                            else:
                                config.set_format_constraint(Format.NOTHING, True)
                        case _:
                            if is_active == False:
                                raise UncreatableValueException(f"unknown format equal. need to define {format_value}")
                case ConstraintEnum.VALUE_EQUAL_EMPTY_STRING:
                    if is_active:
                        config.empty_string = True
                    else :
                        config.except_string_list.append(rule.constraint.values[0])
                case ConstraintEnum.ENCODING_EQUAL:
                    for value in rule.constraint.values:
                        match value.lower():
                            case "pem":
                                if is_active:
                                    config.set_format_constraint(Format.PEM)
                                else:
                                    config.set_format_constraint(Format.NOTHING,True)
                            case "base64":
                                if is_active:
                                    config.base64_encoding = True
                                else:
                                    config.base64_encoding = False
                case ConstraintEnum.PREFIX_NOT_EQUAL:
                    for value in rule.constraint.values:
                        if is_active:
                            config.not_allow_prefix_set.add(value)
                        else:
                            config.allow_prefix_set.add(value)
                case ConstraintEnum.NOT_LEADING_ZEROS:
                    if is_active:
                        config.not_allow_prefix_set.add("0")
                    else:
                        config.allow_prefix_set.add("0")
                case ConstraintEnum.VALUE_EQUAL:
                    if is_active:
                        config.equal_value = rule.constraint.values[0]
                    else :
                        config.except_string_list.append(rule.constraint.values[0])
                case ConstraintEnum.VALUE_NOT_EQUAL:
                    if is_active:
                        config.except_string_list.append(rule.constraint.values[0])
                    else:
                        return rule.constraint.values[0]
                case ConstraintEnum.SPEC_IN_ISO15118:
                    if is_active:
                        config.enum_list = ISO_version_list
                    else:
                        for value in ISO_version_list:
                            config.except_string_list.append(value)
                case ConstraintEnum.DECIMAL_PLACES_MAX:
                    if is_active:
                        config.max_decimal_places = int(rule.constraint.values[0])
                    else:
                        config.max_decimal_places = int(rule.constraint.values[0]) + random.randint(1, 20)
                case ConstraintEnum.VALUE_FROM_MEASUREMENTS_APPENDICES:
                    for name in self.parser.standardized_units_of_measure_parser.get_name_list():
                        if is_active:
                            config.enum_list.append(name)
                        else:
                            config.except_string_list.append(name)
                case ConstraintEnum.CHARACTER_SET_IN:
                    if is_active:
                        config.population_constraint.set(
                            value= self.generate_limit_charset_random_string(rule.constraint.values),
                            level = 2
                        )
                    else:
                        result = self.expand_charset(rule.constraint.values)
                        config.not_allowed_characters.extend(result)
                        config.population_constraint.set(
                            value=self.generate_limit_charset_random_string(rule.constraint.values, COMMON_UNICODE_PRINTABLES),
                            level=999
                        )
                case ConstraintEnum.REPRESENTATION_EQUAL:
                    value = rule.constraint.values[0].lower()
                    match value:
                        case "camel case":
                            if is_active == True:
                                config.not_allowed_characters.append("-")
                                config.not_allowed_characters.append("_")
                            else:
                                config.required_characters.append("-")
                                config.required_characters.append("_")
                        case _:
                            print("unknown constraint representation value in generate_string_value function:")
                            print(rule)
                            continue
                case ConstraintEnum.VALUE_FROM_STANDARDIZED_COMPONENT_NAMES:
                    for name in self.parser.summary_list_of_standardized_components_parser.get_name_list():
                        if is_active:
                            config.enum_list.append(name)
                        else:
                            config.except_string_list.append(name)
                case ConstraintEnum.VALUE_FROM_STANDARDIZED_VARIABLE_NAMES:
                    for name in self.parser.standardized_variables_parser.get_name_list():
                        if is_active:
                            config.enum_list.append(name)
                        else:
                            config.except_string_list.append(name)
                case ConstraintEnum.REMOVE_FIELD_EQUAL_TRUE:
                    if is_active == True:
                        config.remove = True
                    else:
                        config.required = True
                case ConstraintEnum.VALUE_FROM_SECURITY_EVENTS_LIST:
                    for name in self.parser.security_events_parser.get_name_list():
                        if is_active:
                            config.enum_list.append(name)
                        else:
                            config.except_string_list.append(name)
                case ConstraintEnum.SENDING_DEPENDS_ON_EQUAL:
                    value_split_list = rule.constraint.values[0].split(".")
                    if value_split_list[0] == "variable":
                        value = self.context.get_variable_value(value_split_list[-2], value_split_list[-1])
                        if value:
                            match value:
                                case "Never":
                                    if is_active:
                                        config.empty_string = True
                                    else:
                                        config.required = True
                                case "OncePerTransaction":
                                    sent_public_key = self.context.sent_public_key()
                                    if is_active:
                                        if sent_public_key:
                                            config.empty_string = True
                                    else:
                                        if sent_public_key:
                                            config.required = True
                                case "EveryMeterValue":
                                    if is_active:
                                        config.required = True
                                    else:
                                        return ""
                        elif not is_active:
                            raise UncreatableValueException(f"ConstraintEnum.SENDING_DEPENDS_ON_EQUAL {rule.constraint.values[0]} is empty")
                case ConstraintEnum.CAN_VERIFICATION_EQUAL:
                    if not "signedMeterData" in property_value_generate_config.result:
                        if "signedMeterData" in property_value_generate_config.used_property_key_set:
                            continue
                        raise ForceConditionException(
                            message="force condition list is not empty",
                            force_condition_list=[
                                Condition(
                                    target="field.signedMeterData",
                                    attribute="notEmpty",
                                    operator="equal",
                                    values=["true"]
                                )
                            ]
                        )
                    signed_meter_data = property_value_generate_config.result["signedMeterData"]
                    if signed_meter_data and not isinstance(signed_meter_data, list) and not isinstance(signed_meter_data, dict):
                        signature = self.signature_dict.get(signed_meter_data)
                        if signature and isinstance(signature, Signature):
                            if is_active:
                                config.signature = signature
                            else:
                                config.except_string_list.append(signature.get_public_key())
                case ConstraintEnum.SIGNED_WITH_AND:
                    if not "signingMethod" in property_value_generate_config.result:
                        if "signingMethod" in property_value_generate_config.used_property_key_set:
                            continue
                        raise ForceConditionException(
                            message="force condition list is not empty",
                            force_condition_list=[
                                Condition(
                                    target="field.signingMethod",
                                    attribute="notEmpty",
                                    operator="equal",
                                    values=["true"]
                                )
                            ]
                        )
                    if not "encodingMethod" in property_value_generate_config.result:
                        if "encodingMethod" in property_value_generate_config.used_property_key_set:
                            continue
                        raise ForceConditionException(
                            message="force condition list is not empty",
                            force_condition_list=[
                                Condition(
                                    target="field.encodingMethod",
                                    attribute="notEmpty",
                                    operator="equal",
                                    values=["true"]
                                )
                            ]
                        )
                    signing_method = property_value_generate_config.result["signingMethod"]
                    encoding_method = property_value_generate_config.result["encodingMethod"]

                    if is_active:
                        if signing_method in CITRINE_SIGNED_METHOD and encoding_method in CITRINE_ENCODING_METHOD:
                            signature = Signature(signing_method=signing_method, encoding_method=encoding_method)
                            config.enum_list = [signature.get_signed_meter_data()]
                            self.signature_dict[signature.get_signed_meter_data()] = signature
                    else:
                        pass
                case _:
                    if is_active == False:
                        raise UncreatableValueException("unknown constraint in generate_string_value")

        if config.byte_fix_excluded_lengths:
            min_length = None
            max_length = None
            possible_lengths = None
            try:
                min_length = PayloadGenerator.DEFAULT_MIN_LENGTH if config.min_length_constraint is None else config.min_length_constraint.length
                max_length = PayloadGenerator.DEFAULT_MAX_LENGTH if config.max_length_constraint is None else config.max_length_constraint.length
                possible_lengths = [i for i in range(min_length, max_length) if i not in config.byte_fix_excluded_lengths]
                fix_length = random.choice(possible_lengths)
                config.min_length_constraint = MinLengthConstraint.update(
                    constraint=config.min_length_constraint,
                    length=fix_length,
                    force=True
                )
                config.max_length_constraint = MaxLengthConstraint.update(
                    constraint=config.max_length_constraint,
                    length=fix_length,
                    force=True
                )
            except IndexError as e:
                print(f"index error occur:: {min_length} / {max_length}")
                print(possible_lengths)

        MAX_TRY_COUNT = 200
        while_cnt = 0
        generate_value_result = None
        if property_value_generate_config.property_key == "triggerReason" and self.context.ev_connection_trigger:
            return random.choice(self.context.ev_connection_trigger_reason_list)

        while while_cnt < MAX_TRY_COUNT:
            while_cnt += 1
            generate_value_result = self.generate_random_string_value(config)

            if config.except_string_list and (
                    not generate_value_result or generate_value_result in config.except_string_list):
                continue
            break
        else:
            raise UncreatableValueException(f"except_string_list : {generate_value_result} / {config.except_string_list} / {self.used_token_set}")

        if generate_value_result != "":
            if property_value_generate_config.property_key == "idToken":
                type_value = property_value_generate_config.result.get("type")
                self.test_controller_manager.insert_id_token(generate_value_result, type_value)
            if self.context:
                if property_value_generate_config.property_key == "eventType":
                    self.context.set_event_type(generate_value_result)
                if property_value_generate_config.property_key == "triggerReason":
                    self.context.set_trigger_reason(generate_value_result)
        return generate_value_result

    def insert_at_random_position(self, original: str, to_insert: str) -> str:
        position = random.randint(0, len(original))
        return original[:position] + to_insert + original[position:]

    def is_active_rule(self, rule, property_value_generate_config:PropertyValueGenerateConfig):
        result = self.is_determine_rule(rule) == False
        if result == False:
            print(f"determine_rule affect {property_value_generate_config.property_key}")
            self.determine_hit = True
        return result

    def has_determine_value(self, data):
        if isinstance(data, (list, set, tuple)):
            for item in data:
                if self.has_determine_value(item):
                    return True
        elif isinstance(data, dict):
            for key, value in data.items():
                if key == "rules":
                    if isinstance(value, (set, list, tuple)):
                        for rule in value:
                            if self.is_determine_rule(rule):
                                return True
                    elif isinstance(value, dict):
                        for rule in value.values():
                            if self.is_determine_rule(rule):
                                return True
                    else:
                        if self.is_determine_rule(value):
                            return True
                if self.has_determine_value(value):
                    return True
        else:
            if hasattr(data, "__iter__") and not isinstance(data, (str, bytes)):
                for item in data:
                    if self.has_determine_value(item):
                        return True
        return False

    def is_definitely_base64(self, s: str) -> bool:
        try:
            # base64 decode (strict mode)
            decoded = base64.b64decode(s, validate=True)

            # re-encode and compare (with and without padding)
            re_encoded = base64.b64encode(decoded).decode()

            # remove padding for comparison if original string lacks it
            return s == re_encoded or s.rstrip('=') == re_encoded.rstrip('=')
        except (binascii.Error, ValueError):
            return False

    def generate_array_value(self, property_value_generate_config: PropertyValueGenerateConfig):
        if property_value_generate_config.property_value["item"]:
            min_item_constraint: MinItemConstraint = None
            max_item_constraint: MaxItemConstraint = None
            is_content_configured_by_measurands = False
            measurand_set = set()

            for rule in property_value_generate_config.property_value["rules"]:
                is_active: bool = self.is_active_rule(rule, property_value_generate_config)
                if rule.conditions is not None:
                    if self.check_condition_hit(rule, is_active, property_value_generate_config) == False:
                        continue

                match ConstraintDefine.getConstraintEnum(rule.constraint):
                    case ConstraintEnum.MIN_ITEMS_EQUAL:
                        min_item_size = int(rule.constraint.values[0])
                        if is_active:
                            min_item_constraint = MinItemConstraint.update(
                                constraint=min_item_constraint,
                                size=int(min_item_size),
                                force=False
                            )
                        else:
                            if min_item_size >= 1:
                                random_size = random.randint(0, min_item_size - 1) if min_item_size > 0 else 0
                                min_item_constraint = MinItemConstraint.update(
                                    constraint=min_item_constraint,
                                    size=int(random_size),
                                    force=True
                                )
                                max_item_constraint = MaxItemConstraint.update(
                                    constraint=max_item_constraint,
                                    size=int(random_size),
                                    force=True
                                )
                            else:
                                raise UncreatableValueException(f"Min item size {min_item_size} is an uncreatable value")
                    case ConstraintEnum.MAX_ITEMS_EQUAL:
                        value = None
                        max_item_size = None
                        try:
                            max_item_size = int(rule.constraint.values[0])
                        except ValueError:
                            value_split_list = rule.constraint.values[0].split(".")
                            if value_split_list[0] == "variable":
                                value = self.context.get_variable_value(value_split_list[-2], value_split_list[-1])
                                if value is None:
                                    if is_active == False:
                                        raise UncreatableValueException(
                                            f"Can't read variable {value_split_list[-2]}.{value_split_list[-1]}")
                                else:
                                    max_item_size = int(value)
                            if max_item_size is None:
                                continue
                        if is_active:
                            max_item_constraint = MaxItemConstraint.update(
                                constraint=max_item_constraint,
                                size=int(max_item_size),
                                force=False
                            )
                        else:
                            new_max_size = max_item_size + 2
                            min_item_size = max_item_size + 1
                            min_item_constraint = MinItemConstraint.update(
                                constraint=min_item_constraint,
                                size=int(min_item_size),
                                force=True
                            )
                            max_item_constraint = MaxItemConstraint.update(
                                constraint=max_item_constraint,
                                size=int(new_max_size),
                                force=True
                            )
                    case ConstraintEnum.TYPE_EQUAL:
                        if is_active == False:
                            return self.create_simple_value_with_except_type(["array"])
                    case ConstraintEnum.REQUIRED_EQUAL_TRUE:
                        if is_active == False:
                            return PayloadGenerator.EMPTY_VALUE
                    case ConstraintEnum.CONTENT_CONFIGURED_BY:
                        measurand_set = self.get_measurand_config_value_set(rule.constraint.values)
                        if not len(measurand_set) > 0:
                            for value in rule.constraint.values:
                                default_value = get_default_measurand(value)
                                if default_value is not None:
                                    measurand_set.add(default_value)
                        if is_active:
                            is_content_configured_by_measurands = True
                        else:
                            if measurand_set:
                                property_value_generate_config.force_not_in_measurand_set = measurand_set
                            else:
                                if "variable.SampledDataCtrlr.TxEndedMeasurands" not in rule.constraint.values:
                                    print(rule)
                                    exit()
                                raise UncreatableValueException(f"ConstraintEnum.CONTENT_CONFIGURED_BY: measurand_set is empty {rule.constraint.values}")
                    case _:
                        if is_active == False:
                            raise UncreatableValueException("unknown constraint in generate_array_value")
            min_item_size = min_item_constraint.size if min_item_constraint else PayloadGenerator.DEFAULT_MIN_SIZE
            max_item_size = max_item_constraint.size if max_item_constraint else PayloadGenerator.DEFAULT_MAX_SIZE
            # size..over
            fix_item_size = min_item_size
            if fix_item_size > 1000:
                raise UncreatableValueException("1000 over array is not Supported")

            result = []
            for _ in range(fix_item_size):
                config = PropertyValueGenerateConfig(
                    parent_key=property_value_generate_config.parent_key,
                    property_key=property_value_generate_config.property_key,
                    property_value=property_value_generate_config.property_value["item"],
                    force_measurand= random.choice(list(measurand_set)) if is_content_configured_by_measurands and measurand_set else None,
                    force_not_in_measurand_set=property_value_generate_config.force_not_in_measurand_set
                )

                value = self.property_value_generate(config)
                while value == PayloadGenerator.EMPTY_VALUE:
                    value = self.property_value_generate(config)
                result.append(value)
            return result
        else:
            print("Undefined generate array:")

    def get_measurand_config_value_set(self, values):
        result = set()
        for value in values:
            value_split_list = value.split(".")
            if value_split_list[0] == "variable":
                value = self.context.get_variable_value(value_split_list[-2], value_split_list[-1])
                if value:
                    for split_value in value.split(","):
                        result.add(split_value)
            else:
                print(f"unknown CONFIGURED_BY:: {value_split_list[0]}")
        return result
    def generate_object_value(self, property_value_generate_config:PropertyValueGenerateConfig):
        required = False
        remove = False
        for rule in property_value_generate_config.property_value["rules"]:
            is_active = self.is_active_rule(rule, property_value_generate_config)
            if rule.conditions is not None:
                if self.check_condition_hit(rule, is_active, property_value_generate_config) == False:
                    continue

            constraint_enum = ConstraintDefine.getConstraintEnum(rule.constraint)
            match constraint_enum:
                case ConstraintEnum.JAVA_TYPE_EQUAL:
                    if is_active == False:
                        return self.create_simple_value_with_except_type(["object"])
                case ConstraintEnum.TYPE_EQUAL:
                    if is_active == False:
                        return self.create_simple_value_with_except_type(["object"])
                case ConstraintEnum.REQUIRED_EQUAL_TRUE | ConstraintEnum.IMPLEMENTED_EQUAL_TRUE:
                    if is_active == False:
                        return PayloadGenerator.EMPTY_VALUE
                    else:
                        required = True
                case ConstraintEnum.REMOVE_FIELD_EQUAL_TRUE:
                    if is_active == True:
                        remove = True
                    else:
                        required = True
                case ConstraintEnum.CHARGING_PROFILE_PURPOSE_EQUAL:
                    value = rule.constraint.values[0]
                    choice_values = ["TxDefaultProfile", "ChargingStationMaxProfile", " ChargingStationExternalConstraints","TxProfile"]
                    if is_active == True:
                        self.fix_value_container.set_value(parent_key="chargingProfile", field_name="chargingProfilePurpose", value=value)
                    else:
                        available = [c for c in choice_values if c != value]
                        pick = random.choice(available)
                        self.fix_value_container.set_value(parent_key="chargingProfile",
                                                           field_name="chargingProfilePurpose", value=pick)
                case ConstraintEnum.ONCE_PER_TRANSACTION_EQUAL_TRUE:
                    if property_value_generate_config.property_key == "idToken":
                        if is_active == False:
                            started_id_token = self.context.get_started_id_token()
                            if not started_id_token:
                                raise UncreatableValueException(f"ONCE_PER_TRANSACTION_EQUAL_TRUE not exist start idtoken")
                            self.context.set_force_event_type("Updated")
                            return started_id_token

                    else:
                        raise UncreatableValueException(f"ONCE_PER_TRANSACTION_EQUAL_TRUE unknown constraint {property_value_generate_config.property_key}")
                case _:
                    if is_active == False:
                        raise UncreatableValueException("unknown constraint in property_value_generate Object")
        if property_value_generate_config.property_key == "evse" and self.context.ev_connection_trigger:
            required = True

        if self.context.required_id_token_constraint and property_value_generate_config.property_key == "idToken" and property_value_generate_config.parent_key == "TransactionEventRequest":
            required = True

        if self.has_determine_value(property_value_generate_config.property_value) == False and not required:
            if remove or random.choice([True, False]):
                return PayloadGenerator.EMPTY_VALUE

        return self.make_seed(property_value_generate_config.property_key, property_value_generate_config.property_value, force_measurand=property_value_generate_config.force_measurand, force_not_in_measurand_list=property_value_generate_config.force_not_in_measurand_set)

    def property_value_generate(self, property_value_generate_config:PropertyValueGenerateConfig):
        if property_value_generate_config and "info" in property_value_generate_config.property_value:
            fix_value = None
            if self.fix_value_container:
                fix_value =  self.fix_value_container.get_value(
                    parent_key=property_value_generate_config.parent_key,
                    field_name=property_value_generate_config.property_key
                )
            if fix_value is not None and not self.has_determine_value(property_value_generate_config.property_value):
                return fix_value
            match property_value_generate_config.property_value["info"].type:
                case "object":
                    return self.generate_object_value(property_value_generate_config)
                case "array":
                    return self.generate_array_value(property_value_generate_config)
                case "string":
                    return self.generate_string_value(property_value_generate_config)
                case "integer":
                    return self.generate_integer_value(property_value_generate_config)
                case "number":
                    return self.generate_number_value(property_value_generate_config)
                case "boolean":
                    return self.generate_boolean_value(property_value_generate_config)
                case None:
                    return self.create_simple_value_with_except_type()
                case _:
                    print(f"unmatch type: {property_value_generate_config.property_value['info'].type}")

    def make_properties_seed(self, object_name, properties, result=None, used_property_key_set=None, force_measurand = None, force_not_in_measurand_list = None) -> MakePropertiesSeedResult:
        if used_property_key_set is None:
            used_property_key_set = set()
        if result is None:
            result = {}
        wait_for_another_property_used_key_list = []

        for property_key, property_value in properties.items():
            if object_name == "AuthorizeRequest":
                if property_key in ["certificate", "iso15118CertificateHashData"]:
                    if self.has_determine_value(property_value):
                        raise UncreatableValueException(f"OCSP Related Value is not range")
                    continue


            if property_key in result:
                continue
            used_property_key_set.add(property_key)
            property_value_generate_config = PropertyValueGenerateConfig(
                parent_key=object_name,
                parent_value=properties,
                property_key=property_key,
                property_value=property_value,
                result=result,
                used_property_key_set=used_property_key_set,
                force_measurand= force_measurand,
                force_not_in_measurand_set= force_not_in_measurand_list
            )
            try:
                gen_property_value = self.property_value_generate(property_value_generate_config)
                if gen_property_value is PayloadGenerator.EMPTY_VALUE:
                    pass
                else:
                    result[property_key] = gen_property_value
            except WaitForAnotherPropertyUsedException as e:
                wait_for_another_property_used_key_list.append(property_key)
            except ForceConditionException as e:
                wait_for_another_property_used_key_list.append(property_key)
                for condition in e.force_condition_list:
                    condition_enum = ConditionDefine.getConditionEnum(condition)
                    field_name = condition.get_target_name()

                    match condition_enum:
                        case ConditionEnum.VALUE_IN:
                            result[field_name] = random.choice(condition.values)
                        case ConditionEnum.VALUE_EQUAL:
                            result[field_name] = random.choice(condition.values)
                        case ConditionEnum.VALUE_NOT_EQUAL:
                            result_value = None
                            while result_value is None or result_value in condition.values:
                                config = PropertyValueGenerateConfig(
                                    parent_key=object_name,
                                    parent_value=properties,
                                    property_key=field_name,
                                    property_value=properties.get(field_name),
                                    result=result,
                                    used_property_key_set=used_property_key_set,
                                    force_measurand = force_measurand,
                                    force_not_in_measurand_set= force_not_in_measurand_list
                                )
                                print(f"field_name: {field_name}")
                                print(condition.values)
                                result_value = self.property_value_generate(config)
                            result[field_name] = result_value
                        case ConditionEnum.PROVIDED_EQUAL_FALSE:
                            result.pop(field_name, None)
                        case ConditionEnum.NOT_EMPTY_EQUAL_TRUE:
                            pass
                        case _:
                            print("unknown force condition in make seed")
                            print(e.force_condition_list)
                            continue
            except UncreatableValueException as e:
                print("raise uncreatable value exception")
                raise e

        return MakePropertiesSeedResult(
            result=result,
            wait_for_another_property_used_key_list = wait_for_another_property_used_key_list,
            used_property_key_set = used_property_key_set
        )

    def make_seed(self, object_name, data, force_property_set = None, force_measurand = None, force_not_in_measurand_list = None):
        if isinstance(data, dict) and "properties" in data:
            properties = data["properties"]

            make_properties_seed_result:MakePropertiesSeedResult = self.make_properties_seed(object_name, properties, force_property_set, force_measurand = force_measurand, force_not_in_measurand_list = force_not_in_measurand_list)
            loop_cnt = 0
            while make_properties_seed_result.wait_for_another_property_used_key_list:
                loop_cnt += 1
                make_properties_seed_result = self.make_properties_seed(object_name, properties, make_properties_seed_result.result, make_properties_seed_result.used_property_key_set, force_measurand = force_measurand, force_not_in_measurand_list= force_not_in_measurand_list)

                if loop_cnt > 20:
                    raise UncreatableValueException(f"[wait_for_another_property_used_key_list]loop count exceeded {make_properties_seed_result.wait_for_another_property_used_key_list}", )
            return make_properties_seed_result.result
        return None

