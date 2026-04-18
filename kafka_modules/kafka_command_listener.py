from kafka import KafkaConsumer
import asyncio
from kafka_modules.kafka_command_message import KafkaCommandMessage
from confluent_kafka import Consumer, KafkaError

class KafkaCommandListener:
    def __init__(self, topic, controller_manager):
        self.topic = topic
        self.controller_manager = controller_manager
        self.consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'ocpp-simulator-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True
        })
        self.consumer.subscribe([self.topic])
        self._running = True

    async def listen(self):
        print(f"📡 Kafka listening on topic: {self.topic}")
        loop = asyncio.get_event_loop()

        while self._running:
            msg = await loop.run_in_executor(None, self.consumer.poll, 1.0)

            if msg is None:
                await asyncio.sleep(0.1)
                continue

            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"⚠ Kafka error: {msg.error()}")
                continue

            try:
                decoded = msg.value().decode("utf-8")
                command_message: KafkaCommandMessage = KafkaCommandMessage.from_json(decoded)
                print(f"[✅ Message received] {decoded}")
                await self.controller_manager.command_process(command_message)
            except Exception as e:
                print(f"[❌ Handler error] {e}")

    def stop(self):
        self._running = False
        self.consumer.close()