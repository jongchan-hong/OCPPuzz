from kafka import KafkaProducer
import json

from constants.ocpp_version import OcppVersion
from kafka_modules.kafka_command_message import KafkaCommandMessage, KafkaCommandEnum

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: v.encode('utf-8')
)

message = KafkaCommandMessage(
    command=KafkaCommandEnum.RULE_BASED_RANDOM,
    ocpp_version=OcppVersion.version_201,
    gen_cnt=1000
)

producer.send("charger-commands", message.to_json())
producer.flush()
print("[Kafka] Command Send")