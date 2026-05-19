from time import sleep
from typing import Optional
from sqlalchemy import create_engine, MetaData, Table, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, func
from datetime import datetime
import subprocess
import json
from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from storage.entity.citrine.evse_entity import EvseEntity
from storage.entity.citrine.id_token_entity import IdTokenEntity, AuthorizationEntity
from sqlalchemy import and_
import docker
import time
import requests

from storage.entity.variable_entity import VariableEntity
from generator_modules.format.RFC3339 import RFC3339
from test_controller_modules.test_project_controller.project_event_controller import ProjectEventController
from storage.db_engine import engine
from storage.entity.base_entity import get_session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class CitrineEventController(ProjectEventController):
    id_token_length = 255
    project_name = "Citrine"
    CS_NAME = "Citrine"
    ws_port = 8081
    socket_uri = f"ws://localhost:{ws_port}"
    api_port = 8080
    dump_coverage_port = 9999
    api_uri = f"http://localhost:{api_port}/ocpp/2.0.1/"
    dump_coverage_uri = f"http://localhost:{dump_coverage_port}/v8dump"
    support_csms_to_cs_trigger = True
    execution_coverage_collect = False

    end_point_group = {
        "Transaction": [
            "CostUpdated",
            "GetTransactionStatus",
        ],
        "Certificates": [
            "CertificateSigned",
            "InstallCertificate",
            "GetInstalledCertificateIds",
            "DeleteCertificate"
        ],
        "Configuration": [
            "SetNetworkProfile",
            "ClearDisplayMessage",
            "GetDisplayMessages",
            "PublishFirmware",
            "SetDisplayMessage",
            "UnpublishFirmware",
            "UpdateFirmware",
            "Reset",
            "ChangeAvailability",
            "TriggerMessage"
        ],
        "EVDriver": [
            "RequestStartTransaction",
            "RequestStopTransaction",
            "CancelReservation",
            "ReserveNow",
            "UnlockConnector",
            "ClearCache",
            "SendLocalList",
            "GetLocalListVersion",
        ],
        "Monitoring": [
            "SetVariableMonitoring",
            "ClearVariableMonitoring",
            "SetMonitoringLevel",
            "SetMonitoringBase",
            "SetVariables",
            "GetVariables",
        ],
        "Reporting":[
            "GetBaseReport",
            #"GetReport",
            "GetMonitoringReport",
            "GetLog",
            "CustomerInformation",
        ],
        "SmartCharging": [
            "ClearChargingProfile",
            "GetChargingProfiles",
            "SetChargingProfile",
            "ClearedChargingLimit",
            "GetCompositeSchedule",
        ],
    }

    def get_restart_container_name_list(self):
        client = docker.from_env()
        return [client.containers.get(self.api_container_name)]

    @staticmethod
    def is_support_api(message_name):
        normalized_name = message_name.removesuffix("Request").removesuffix("Response")
        for group_name, messages in CitrineEventController.end_point_group.items():
            if normalized_name in messages:
                return True
        return False

    def get_end_point(self, message_name:str):
        normalized_name = message_name.removesuffix("Request").removesuffix("Response")
        group_name = self.get_group_name(normalized_name)
        if not group_name:
            return None

        return group_name.lower() + "/" +normalized_name[0].lower() + normalized_name[1:]

    def get_group_name(self, normalized_name):
        for group_name, messages in self.end_point_group.items():
            if normalized_name in messages:
                return group_name
        return None

    def _db_init(self):
        self.db_engine = create_engine("postgresql+psycopg2://citrine:citrine@localhost:5432/citrine")
        self.metadata = MetaData()
        Session = sessionmaker(bind=self.db_engine)
        self.project_session = Session()

    def coverage_init(self):
        MAX_RETRY = 10
        for attempt in range(MAX_RETRY):
            try:
                addr = self.dump_coverage_uri+ "?init=1"
                print(f"addr: {addr}")
                response = requests.get(addr, timeout=10)
                if response.status_code == 200:
                    return True
            except requests.RequestException as e:
                print(f"[Error] Attempt {attempt + 1}: {e}")
                sleep(2)
        return False

    def get_project_name(self)->str:
        return self.project_name

    def dump_coverage_request(self) -> bool:
        MAX_RETRY = 10
        for attempt in range(MAX_RETRY):
            try:
                response = requests.get(self.dump_coverage_uri, timeout=10)
                if response.status_code == 200:
                    return True
            except requests.RequestException as e:
                print(f"[Error] Attempt {attempt + 1}: {e}")
                sleep(2)
        return False

    def get_total_coverage(self)->TotalCoverageDTO:
        coverage_info_dto = self.collect_coverage_total_info()
        return TotalCoverageDTO(
            total_statements= coverage_info_dto.statements.total,
            covered_statements=coverage_info_dto.statements.covered,
            total_branches=coverage_info_dto.branches.total,
            covered_branches=coverage_info_dto.branches.covered,
        )


    def collect_coverage_total_info(self) -> Optional[CoverageInfoDTO]:
        if not self.dump_coverage_request():
            print(f"[{self.project_name}][Error] can't dump!!")
            return None
        container_name = self.api_container_name
        file_path = "/usr/local/apps/citrineos/coverage/report/coverage-summary.json"
        cmd = ["docker", "exec", container_name, "cat", file_path]
        time.sleep(2)
        for _ in range(300):
            try:
                output = subprocess.check_output(cmd, encoding='utf-8')
                json_data = json.loads(output)
                return CoverageInfoDTO(**json_data["total"])
            except subprocess.CalledProcessError:
                time.sleep(0.1)
        else:
            raise FileNotFoundError("create coverage-summary.json fail")
        return None


    def set_variables(self, set_variable_data_list):
        result = self.send_message_end_point(
            message_name="SetVariablesRequest",
            payload={
                "setVariableData": set_variable_data_list
            }
        )
        cnt = 0
        for _ in range(60):
            sleep(0.2)
            with get_session() as db_session:
                cnt += 1
                print(f"cnt:: {cnt}")
                wait_entity = db_session.query(VariableEntity).filter(
                    VariableEntity.cs_name == self.CS_NAME
                ) \
                    .order_by(desc(VariableEntity.created_at)).first()
                if wait_entity:
                    sleep(1)
                    return result

    def get_uri(self) -> str:
        return self.socket_uri + "/" + self.CS_NAME

    def request_api(self, end_point, payload):
        server_url = self.api_uri + end_point
        querystring = {
            "identifier": self.CS_NAME,
            "tenantId": "T01"
        }
        headers = {
            "Content-Type": "application/json"
        }

        for retry in range(3):
            try:
                response = requests.post(
                    server_url,
                    headers=headers,
                    params=querystring,
                    json=payload,
                    timeout=10
                )
                if response.status_code != 200:
                    print("response status code", response.status_code)
                return response.status_code == 200
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e} (retry {retry + 1}/3)")
                time.sleep(2 ** retry)
            except requests.exceptions.Timeout:
                print("Request timed out (retry {retry + 1}/3)")
                time.sleep(2 ** retry)
        return False

    def set_evse_id(self, evse_id):
        existing = self.project_session.query(EvseEntity).filter(
            and_(
                EvseEntity.id == evse_id
            )
        ).first()

        if not existing:
            evse_entity = EvseEntity(
                id=evse_id,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            self.project_session.add(evse_entity)
            self.project_session.commit()
            return True
        return False

    def publish_firmware_request_to_csms(self, request_id:int) -> bool:
        end_point = "configuration/publishFirmware"
        payload = {
            "requestId": request_id,
            "location": "TestLocation",
            "checksum": "TestChecksum",
        }
        return self.request_api(end_point, payload)

    def update_firmware_request_to_csms(self, request_id:int) -> bool:
        end_point = "configuration/updateFirmware"
        payload = {
            "requestId": request_id,
            "firmware": {
                "location": "TestLocation",
                "retrieveDateTime": RFC3339.random_generate(3)
            }
        }
        return self.request_api(end_point, payload)

    def __truncate_by_length(self, id_token):
        if len(id_token) > self.id_token_length:
            id_token = id_token[:self.id_token_length]
        return id_token

    def insert_token(self, id_token, type) -> bool:
        id_token = str(id_token)
        type = str(type)
        id_token = self.__truncate_by_length(id_token)
        type = self.__truncate_by_length(type)

        existing = self.project_session.query(IdTokenEntity).filter(
            and_(
                IdTokenEntity.idToken == id_token,
                IdTokenEntity.type == type
            )
        ).first()

        if not existing:
            token = IdTokenEntity(idToken=id_token, type=type)
            self.project_session.add(token)
            self.project_session.commit()

            authorization = AuthorizationEntity(
                allowedConnectorTypes=[],
                disallowedEvseIdPrefixes=[],
                idTokenId=token.id,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            self.project_session.add(authorization)
            self.project_session.commit()

            return True

        return False
    def send_message_end_point(self, message_name, payload):
        end_point = self.get_end_point(message_name)
        if not end_point:
            return None
        return self.request_api(end_point, payload)

    def register_charging_station_info(self) ->bool:
        try:
            charging_stations = Table("ChargingStations", self.metadata, autoload_with=self.db_engine)

            with self.db_engine.connect() as conn:
                stmt = select(charging_stations.c.id).where(charging_stations.c.id == self.CS_NAME)
                if conn.execute(stmt).first():
                    return True

                values = {
                    "id": self.CS_NAME,
                    "isOnline": True,
                    "protocol": "ocpp2.0.1",
                    "createdAt": func.now(),
                    "updatedAt": func.now(),
                }

                insert_stmt = insert(charging_stations).values(values)
                conn.execute(insert_stmt)
                conn.commit()

            return True

        except SQLAlchemyError as e:
            print(f"[ERROR] ChargingStation insert failed: {type(e).__name__}: {e}")
            return False