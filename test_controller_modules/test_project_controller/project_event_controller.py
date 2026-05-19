from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import json
from sqlalchemy import desc, func
from dto.call import Call
from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from storage.entity.base_entity import get_session
from sqlalchemy import text
import asyncio
from storage.entity.coverage_info_entity import CoverageInfoEntity
from storage.entity.generate_message_entity import GenerateMessageEntity
from storage.entity.send_trigger_entity import SendTriggerEntity
from storage.entity.test_coverage_entity import TestCoverageEntity
from storage.entity.test_execution_entity import TestExecutionEntity
import websocket
from constants.controller_status import ControllerStatus
import threading
import platform
import subprocess
import traceback
import time
import base64
import uuid
from storage.entity.variable_entity import VariableEntity
from xml.etree import ElementTree as ET
from sqlalchemy.orm import sessionmaker
from storage.db_engine import engine
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class ProjectEventController(ABC):
    support_csms_to_cs_trigger = False
    connected = False
    authorization = False
    socket_uri = ""
    project_name = ""
    package_name = "entity"
    test_execution_entity_list = []
    api_port = 0
    ws_port = 0
    execution_coverage_collect = False

    def __init__(self, test_controller_manager):
        self.waiting_msg_ids = set()
        self.test_controller_manager = test_controller_manager
        self._db_init()
        self.coverage_init()
        self.api_container_name = self.get_container_name_by_port(self.api_port)
        self.ws_container_name = self.get_container_name_by_port(self.ws_port)


    @abstractmethod
    def _db_init(self):
        pass

    @abstractmethod
    def coverage_init(self):
        pass

    @abstractmethod
    def set_variables(self, set_variable_data_list):
        pass

    @abstractmethod
    def get_uri(self) -> str:
        pass

    @abstractmethod
    def get_project_name(self)->str:
        pass

    @abstractmethod
    def get_restart_container_name_list(self):
        pass

    def restart_csms_server(self):
        print(f"[{self.project_name}] restart_ocpp_server sleep 3..")
        time.sleep(3)
        restart_container_list = self.get_restart_container_name_list()
        for container in restart_container_list:
            print(f"[{self.project_name}] before container status = {container.status}")
            if container.status == 'running':
                print(f"[{self.project_name}] Stopping container...")
                container.stop(timeout=60)
                for _ in range(30):
                    container.reload()
                    if container.status == 'exited':
                        break
                    time.sleep(1)
                else:
                    print(f"[{self.project_name}] Container did not exit in time for restart!")
                    continue
            print(f"[{self.project_name}] Starting container...")
            container.start()
            for _ in range(30):
                container.reload()
                if container.status == 'running':
                    break
                time.sleep(1)
            else:
                print(f"[{self.project_name}] Container did not start in time!")
                continue
            time.sleep(10)
            print(f"[{self.project_name}] after container status = {container.status}")
        return True

    @abstractmethod
    def insert_token(self, id_token, type) -> bool:
        pass

    @abstractmethod
    def set_evse_id(self, evse_id) -> bool:
        pass

    @abstractmethod
    def send_message_end_point(self, message_name, payload) -> bool:
        pass

    @abstractmethod
    def dump_coverage_request(self) -> bool:
        pass

    @abstractmethod
    def collect_coverage_total_info(self) -> Optional[CoverageInfoDTO]:
        pass

    @abstractmethod
    def register_charging_station_info(self) -> bool:
        pass

    @abstractmethod
    def get_total_coverage(self)->TotalCoverageDTO:
        pass

    def parse_cobertura(self, file_obj) -> TotalCoverageDTO:
        tree = ET.parse(file_obj)
        root = tree.getroot()
        return TotalCoverageDTO(
            total_statements=int(root.attrib["lines-valid"]),
            covered_statements=int(root.attrib["lines-covered"]),
            total_branches=int(root.attrib["branches-valid"]),
            covered_branches=int(root.attrib["branches-covered"])
        )

    def parse_out(self, file_obj) -> TotalCoverageDTO:
        total_lines = 0
        covered_lines = 0

        for line in file_obj:
            decoded = line.decode("utf-8").strip()

            if not decoded or decoded.startswith("mode:"):
                continue

            parts = decoded.split()
            if len(parts) != 3:
                continue

            try:
                count = int(parts[2])
            except ValueError:
                continue
            file_and_range = parts[0].rsplit(":", 1)
            if len(file_and_range) != 2:
                continue

            line_range = file_and_range[1]
            start_end = line_range.split(",")
            if len(start_end) != 2:
                continue

            try:
                start_line = int(start_end[0].split(".")[0])
                end_line = int(start_end[1].split(".")[0])
            except ValueError:
                continue

            line_span = max(end_line - start_line, 1)
            total_lines += line_span
            if count > 0:
                covered_lines += line_span

        return TotalCoverageDTO(
            total_statements=total_lines,
            covered_statements=covered_lines,
            total_branches=0,
            covered_branches=0
        )

    def save_total_coverage(self, test_entity, session):
        total_coverage_dto = self.get_total_coverage()
        if total_coverage_dto:
            total_coverage_entity = TestCoverageEntity(
                test_entity=test_entity,
                project_name=self.project_name,
                total_coverage_dto=total_coverage_dto
            )
            session.add(total_coverage_entity)
            session.commit()
        else:
            print(f"{self.project_name} coverage empty")

    def on_open(self, ws):
        self.connected = True
        print(f"[{self.project_name}][Connected] WebSocket uri: {self.get_uri()}")
        self.on_open_boot_notification()

    def on_open_boot_notification(self):
        payload = [
            2,
            str(uuid.uuid1()),
            "BootNotification",
            {
                "reason": "PowerUp",
                "chargingStation": {
                    "model": "test_model",
                    "vendorName": "test_vendor_name"
                }

            }
        ]
        self.send_message(json.dumps(payload, ensure_ascii=False))

    def get_container_name_by_port(self, port: int) -> str | None:
        try:
            cmd = f'docker ps --format "{{{{.Names}}}} {{{{.Ports}}}}"'

            output = subprocess.check_output(cmd, shell=True, text=True)

            for line in output.strip().splitlines():
                if f":{port}->" in line:
                    return line.split()[0]

            return None

        except subprocess.CalledProcessError:
            return None

    def on_message(self, ws, message):
        print(f"[{self.project_name}][Received]")
        try:
            parsed_message = json.loads(message)  # str → dict
            message_type_id = parsed_message[0]
            match message_type_id:
                case 2:
                    self.on_call_message(parsed_message)
                case 3 | 4:
                    self.on_response_message(parsed_message)
            print(f"[{self.project_name}][Parsed] dict: {parsed_message}")
        except json.JSONDecodeError as e:
            print(f"[{self.project_name}][Error] JSON Parse Fail: {e}")

    def on_response_message(self, parsed_message):
        if not parsed_message[1] in self.waiting_msg_ids:
            print(f"not exist entity {parsed_message[1]}")
            return

        self.waiting_msg_ids.remove(parsed_message[1])
        session = SessionLocal()
        try:
            test_execution_entity = session.query(TestExecutionEntity).filter_by(
                generate_message_id=parsed_message[1],
                project_name=self.project_name
            ).first()
            if test_execution_entity:
                test_execution_entity.response = parsed_message
                test_execution_entity.response_at = datetime.now()
                session.commit()
            else:
                print(f"Entity not found in DB: {parsed_message[1]} / {self.project_name}")
        except Exception as e:
            session.rollback()
            print("DB error:", e)
        finally:
            session.close()

    def on_call_message(self, parsed_message):
        call = Call(parsed_message)
        with get_session() as db_session:
            try:
                if call.action == "SetVariables":
                    if "setVariableData" in call.payload:
                        for variable_data in call.payload["setVariableData"]:
                            variable_entity = VariableEntity(
                                component_name= variable_data["component"]["name"],
                                variable_name=variable_data["variable"]["name"],
                                values=[variable_data["attributeValue"]],
                                project_name= self.project_name,
                                cs_name=self.CS_NAME
                            )
                            db_session.add(variable_entity)
                            db_session.commit()

                query = db_session.query(SendTriggerEntity) \
                    .join(SendTriggerEntity.generate_message_entity) \
                    .filter(
                    GenerateMessageEntity.action == call.action + "Request",
                    SendTriggerEntity.project_name == self.project_name,
                    SendTriggerEntity.trigger_request == None
                ) \
                    .order_by(desc(SendTriggerEntity.created_at))

                latest_trigger = query.first()

                if latest_trigger:
                    latest_trigger.trigger_request = parsed_message
                    latest_trigger.trigger_request_at = datetime.now()
                else:
                    payload = {
                            "status": "Accepted"
                    }
                    if call.action == "SetVariables":
                        payload = {
                            "setVariableResult": [{
                                "attributeStatus": "Accepted",
                                "component": variable_data["component"],
                                "variable": variable_data["variable"],
                            } for variable_data in call.payload["setVariableData"]]
                        }
                    message = [
                        3,
                        call.message_id,
                        payload
                    ]
                    if call.action == "SetVariables":
                        print("send message!!")
                        print(json.dumps(message, ensure_ascii=False))
                    self.send_message(json.dumps(message, ensure_ascii=False))
                    print(f"[{self.project_name}] Unknown call message received:", str(parsed_message))
            except Exception as e:
                print(f"[{self.project_name}][Error] Commit: {e}")
                traceback.print_exc()
                db_session.rollback()

    def reconnect(self, cs_id = ""):
        if cs_id:
            self.CS_NAME = cs_id
        print(f"[{self.project_name}] Reconnecting with new CS_NAME: {self.CS_NAME}")
        if hasattr(self, 'ws') and self.ws:
            try:
                def close_ws():
                    try:
                        if self.ws.sock:
                            self.ws.sock.settimeout(5)
                        self.ws.close()
                        print(f"[{self.project_name}] Previous WebSocket closed.")
                    except Exception as e:
                        print(f"[{self.project_name}][Error] Failed to close previous WebSocket: {e}")

                close_thread = threading.Thread(target=close_ws)
                close_thread.start()
                close_thread.join(timeout=5)

                if close_thread.is_alive():
                    print(f"[{self.project_name}][Warning] ws.close timeout, forcing release.")
                    self.ws = None
                print(f"[{self.project_name}] Previous WebSocket closed.")
            except Exception as e:
                print(f"[{self.project_name}][Error] Failed to close previous WebSocket: {e}")
        print(f"[{self.project_name}][Info] Try to reconnect {self.CS_NAME}")
        success = self.connect()
        if not success:
            print(f"[{self.project_name}] Reconnect failed.")
        return success

    def connect(self) -> bool:
        if not self.register_charging_station_info():
            print(f"[{self.project_name}][Error] Failed to register charging station information.")
            return False
        try:
            print(f"[{self.project_name}] register ok")
            socket_header = {
                "Sec-WebSocket-Protocol": "ocpp2.0.1"
            }
            if self.authorization:
                username = self.CS_NAME
                password = self.CS_NAME
                credentials = f"{username}:{password}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                socket_header["Authorization"] = f"Basic {encoded_credentials}"
                print(f"authorization:: {socket_header['Authorization']}")

            self.ws = websocket.WebSocketApp(
                self.get_uri(),
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                header=socket_header
            )
            thread = threading.Thread(target=self.ws.run_forever)
            thread.daemon = True
            thread.start()

            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1

            if not self.connected:
                print(f"[{self.project_name}]Connection Fail: timeout {timeout}", self.get_uri())
            if self.connected:
                print(f"[{self.project_name}] Connected Success")
                self.status = ControllerStatus.RUNNING
            return self.connected

        except Exception as e:
            print(f"[{self.project_name}][Exception]: {e}")
            return False

    def get_last_trigger_send_trigger_entity(self, action):
        with get_session() as db_session:
            return db_session.query(SendTriggerEntity) \
                .join(SendTriggerEntity.generate_message_entity) \
                .filter(
                SendTriggerEntity.created_at >= func.now() - text("INTERVAL 15 SECOND"),
                GenerateMessageEntity.action == action,
                SendTriggerEntity.project_name == self.project_name
            ) \
                .order_by(desc(SendTriggerEntity.created_at)) \
                .first()

    def send_message(self, message: str):
        if self.ws and self.connected:
            try:
                self.ws.send(message)
                print(f"[{self.project_name}][Sent]")
            except websocket.WebSocketConnectionClosedException:
                print(f"[{self.project_name}] Socket closed. Attempting to reconnect...")
                self.reconnect(self.CS_NAME)
                self.ws.send(message)

    async def send_message_and_wait(self, entity:TestExecutionEntity, session):
        msg_id = str(entity.generate_message_entity.id)
        print(f"waiting msg ids add {msg_id} / {entity.id}")
        self.waiting_msg_ids.add(msg_id)
        entity.send_at = datetime.now()
        self.send_message(entity.generate_message_entity.get_call_json())
        print(f"SEND: {entity.generate_message_entity.get_call_json()}")
        result = False

        for _ in range(50):
            await asyncio.sleep(0.2)
            with get_session() as db_session:
                wait_entity = db_session.query(TestExecutionEntity).get(entity.id)
                if wait_entity.response:
                    print(f"[{self.project_name}][Response] received for ID: {msg_id}")
                    result = True
                    break
        if self.execution_coverage_collect:
            total_coverage_info_dto: Optional[CoverageInfoDTO] = self.collect_coverage_total_info()
            if not total_coverage_info_dto:
                return False
            total_coverage_info_entity: CoverageInfoEntity = CoverageInfoEntity(
                name="total",
                coverage_info_dto=total_coverage_info_dto,
                test_execution_entity=entity
            )
            session.add(total_coverage_info_entity)
            session.commit()
        if not result:
            entity.error_name = "Timeout 10"
            print(f"[{self.project_name}][Timeout]: {msg_id}")
            session.commit()
            return False
        return True

    async def send_trigger_and_wait(self, generate_message_entity: GenerateMessageEntity, session):
        send_trigger_entity = SendTriggerEntity(
            generate_message_entity=generate_message_entity,
            project_name=self.project_name
        )
        session.add(send_trigger_entity)
        session.commit()

        send_message_result = self.send_message_end_point(
            message_name=generate_message_entity.action,
            payload=generate_message_entity.get_payload_dict()
        )

        if send_message_result:
            for _ in range(20):
                await asyncio.sleep(0.5)
                with get_session() as db_session:
                    search_send_trigger_entity = db_session.query(SendTriggerEntity).filter_by(
                        id = send_trigger_entity.id
                    ).first()
                    if search_send_trigger_entity.trigger_request:
                        print(f"[{self.project_name}][Response received] for send_trigger_entity.{send_trigger_entity.id}")
                        return True
            print(f"[{self.project_name}][Timeout]: {send_trigger_entity.id}")
        return False

    def on_error(self, ws, error):
        print(f"[{self.project_name}][Error] on_error: {error}")
        traceback.print_exc()
        self.test_controller_manager.report_error(type(error).__name__)
        max_retry = 5
        retry_cnt = 0
        while retry_cnt < max_retry:
            if self.reconnect(f"RECONNECT_{int(time.time() * 1000)}"):
                print(f"[{self.project_name}] Reconnected successfully on attempt {retry_cnt + 1}")
                break
            retry_cnt += 1
            print(f"[{self.project_name}] Reconnect attempt {retry_cnt} failed.")
            time.sleep(0.4)

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"[{self.project_name}][Closed] Connection Closed. Code: {close_status_code}, Message: {close_msg}")