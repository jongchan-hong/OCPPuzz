from typing import Dict
from parser_modules.parser import Parser
from constants.version_config import version201
from kafka_modules.kafka_command_listener import KafkaCommandListener
from parser_modules.json.json_schema import get_json_schemas, JsonSchema
import asyncio
from test_controller_modules.test_controller_manager import TestControllerManager
from storage.loader.model_loader import ModelLoader
loader = ModelLoader("storage.entity")
loader.load_models()

async def main():
    print("[Test Controller] Main init")
    print("[Test Controller] Parse Start")
    config = version201
    parser = Parser(config)
    json_schemas: Dict[str, JsonSchema] = get_json_schemas(config.json_schema_folder_path)
    print("[Test Controller] Parse End")
    loop = asyncio.get_running_loop()
    controller_manager = TestControllerManager(
        config=config,
        parser=parser,
        json_schemas=json_schemas,
        loop=loop,
    )
    charger_commands_kafka_listener = KafkaCommandListener("charger-commands", controller_manager)
    await charger_commands_kafka_listener.listen()

if __name__ == "__main__":
    try:
        print("[Test Controller] Start")
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        print("[Test Controller] End")