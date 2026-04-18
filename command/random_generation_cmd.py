from kafka import KafkaProducer
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constants.ocpp_version import OcppVersion
from kafka_modules.kafka_command_message import KafkaCommandMessage, KafkaCommandEnum

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: v.encode('utf-8')
)

message = KafkaCommandMessage(
    command=KafkaCommandEnum.RANDOM,
    ocpp_version=OcppVersion.version_201,
    gen_cnt = 1000
)
producer.send("charger-commands", message.to_json())
producer.flush()
print("[Kafka] Command Send")