from typing import Optional

from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from test_controller_modules.test_project_controller.project_event_controller import ProjectEventController
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, select, insert, MetaData
import docker
import time


class OCPPCoreEventController(ProjectEventController):
    CS_NAME = "CHARGER"
    ws_port = 9281
    socket_uri = f"ws://localhost:{ws_port}/OCPP/"
    api_uri = f"http://localhost:{ws_port}/API/"

    project_name = "OCPPCore"
    authorization = True

    def _db_init(self):
        from urllib.parse import quote_plus
        password = quote_plus("YourStrong@Password1!")
        conn_str = f"mssql+pyodbc://SA:{password}@localhost:1433/OCPP.Core?driver=ODBC+Driver+17+for+SQL+Server"
        self.db_engine = create_engine(conn_str)
        self.metadata = MetaData()
        Session = sessionmaker(bind=self.db_engine)
        self.project_session = Session()

    def coverage_init(self):
        pass

    def get_uri(self) -> str:
        print(f"get uri: {self.socket_uri + self.CS_NAME}")
        return self.socket_uri + self.CS_NAME

    def get_restart_container_name_list(self):
        client = docker.from_env()
        return [client.containers.get(self.ws_container_name)]

    def get_total_coverage(self) -> TotalCoverageDTO:
        self.ws.close()
        client = docker.from_env()
        container = client.containers.get(self.ws_container_name)

        print(f"[{self.project_name}] Stopping container for coverage flush...")
        container.stop(timeout=60)

        for _ in range(60):
            container.reload()
            if container.status == 'exited':
                break
            time.sleep(1)
        else:
            print(f"[{self.project_name}] Container did not exit in time!")
            return None

        container_path = "/app/coverage.cobertura.xml"

        print(f"[{self.project_name}] Copying coverage.cobertura.xml from container...")

        try:
            stream, stat = container.get_archive(container_path)
            import tarfile, io
            container.start()
            for _ in range(60):
                container.reload()
                if container.status == 'running':
                    break
                time.sleep(1)
            else:
                print(f"[{self.project_name}] Container did not start in time!")
                return None
            time.sleep(10)
            self.connect()
            with tarfile.open(fileobj=io.BytesIO(b''.join(stream)), mode='r|*') as tar:
                for member in tar:
                    if member.name.endswith("coverage.cobertura.xml"):
                        with tar.extractfile(member) as f:
                            return self.parse_cobertura(f)
            print(f"[{self.project_name}] Failed to extract coverage file from tar!")
        except Exception as e:
            print(f"[{self.project_name}] Failed to get coverage file: {e}")
        return None

    def get_project_name(self) -> str:
        return self.project_name

    def dump_coverage_request(self) -> bool:
        return True

    def collect_coverage_total_info(self) -> Optional[CoverageInfoDTO]:
        return None

    def insert_token(self, id_token, type) -> bool:
        try:
            charge_tags_table = Table("ChargeTags", self.metadata, autoload_with=self.db_engine)

            with self.db_engine.connect() as conn:
                stmt = select(charge_tags_table.c.TagId).where(
                    charge_tags_table.c.TagId == id_token)
                if conn.execute(stmt).first():
                    return True
                values = {
                    "TagId": id_token,
                    "TagName": id_token
                }

                insert_stmt = insert(charge_tags_table).values(values)
                conn.execute(insert_stmt)
                conn.commit()
            return True
        except Exception as e:
            print(f"[insert_token] Error: {e}")
            return False

    def register_charging_station_info(self) -> bool:
        try:
            charge_point_table = Table("ChargePoint", self.metadata, autoload_with=self.db_engine)

            with self.db_engine.connect() as conn:
                stmt = select(charge_point_table.c.ChargePointId).where(
                    charge_point_table.c.ChargePointId == self.CS_NAME)
                if conn.execute(stmt).first():
                    return True

                values = {
                    "ChargePointId": self.CS_NAME,
                    "Name": self.CS_NAME,
                    "Comment": f"Auto-registered {self.CS_NAME}",
                    "Username": self.CS_NAME,
                    "Password": self.CS_NAME,
                    "ClientCertThumb": None
                }

                insert_stmt = insert(charge_point_table).values(values)
                conn.execute(insert_stmt)
                conn.commit()

            return True
        except Exception as e:
            print(f"[register_charging_station_info] Error: {e}")
            return False

    def get_end_point(self, message_name:str, payload):
        normalized_name = message_name.removesuffix("Request")
        match normalized_name:
            case "Reset":
                return f"{self.api_uri}/Reset/{self.CS_NAME}"
            case "UnlockConnector":
                if "connectorId" not in payload:
                    return
                return f"{self.api_uri}/UnlockConnector/{payload['connectorId']}"
            case _:
                return None

    def request_api(self, end_point):
        headers = {
            "X-API-Key": "36029A5F-B736-4DA9-AE46-D66847C9062C"
        }

        response = requests.get(end_point, headers=headers)
        if response.status_code != 200:
            print("response status code", response.status_code)

        return response.status_code == 200

    def send_message_end_point(self, message_name, payload):
        end_point = self.get_end_point(message_name, payload)
        if not end_point:
            return None
        return self.request_api(end_point)

    def set_evse_id(self, evse_id) -> bool:
        return False

    def set_variables(self, set_variable_data_list):
        pass