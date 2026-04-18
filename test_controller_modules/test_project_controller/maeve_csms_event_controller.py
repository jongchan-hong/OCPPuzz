from typing import Optional

from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from test_controller_modules.test_project_controller.project_event_controller import ProjectEventController
import docker
import time
import requests

from datetime import datetime, timezone

class MaeveCsmsEventController(ProjectEventController):
    CS_NAME = "CHARGER"
    socket_port = 9515
    api_port = 9410
    socket_uri = f"ws://localhost:{socket_port}/ws/"
    api_uri = f"http://localhost:{api_port}/api/v0/"
    project_name = "maeve-csms"
    trigger_message_list = [
        "BootNotification",
        "StatusNotification",
        "SignV2GCertificate",
        "SignChargingStationCertificate",
        "SignCombinedCertificate",
    ]

    def _db_init(self):
        pass

    def coverage_init(self):
        pass

    def get_uri(self) -> str:
        return self.socket_uri + self.CS_NAME

    def get_project_name(self) -> str:
        return self.project_name

    def dump_coverage_request(self) -> bool:
        return True

    def collect_coverage_total_info(self) -> Optional[CoverageInfoDTO]:
        return None

    def get_restart_container_name_list(self):
        client = docker.from_env()
        return [client.containers.get(self.ws_container_name), client.containers.get(self.api_container_name)]

    def get_total_coverage(self)->TotalCoverageDTO:
        self.ws.close()
        client = docker.from_env()
        socket_container = self.get_container_name_by_port(self.api_port)
        container = client.containers.get(socket_container)
        container.exec_run(cmd="/go/stop_server.sh")
        print(f"[{self.project_name}] Executing stop_server.sh...")
        time.sleep(2)
        container_path = "/go/coverage.out"

        print(f"[{self.project_name}] Copying coverage.out from container...")
        stream, stat = container.get_archive(container_path)
        import tarfile, io
        container.exec_run(cmd="/bin/bash /go/start_server.sh", detach=True)
        time.sleep(3)
        self.connect()
        with tarfile.open(fileobj=io.BytesIO(b''.join(stream)), mode='r|*') as tar:
            for member in tar:
                if member.name.endswith("coverage.out"):
                    print(f"member.name: {member.name}")
                    with tar.extractfile(member) as f:
                        print("extractfile init")
                        return self.parse_out(f)
        return None

    def insert_token(self, id_token, type) -> bool:
        url = f"{self.api_uri}token"
        headers = {"Content-Type": "application/json"}

        payload = {
            "countryCode": "st",
            "partyId": "str",
            "type": type,
            "uid": id_token,
            "contractId": "DECGN000020001",
            "visualNumber": "string",
            "issuer": "string",
            "groupId": "string",
            "valid": True,
            "languageCode": "st",
            "cacheMode": "ALWAYS",
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200 or response.status_code == 201
        except requests.RequestException as e:
            print(f"Error posting token: {e}")
            return False

    def register_charging_station_info(self) -> bool:
        url = f"{self.api_uri}cs/{self.CS_NAME}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "securityProfile": 1
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200 or response.status_code == 201
        except requests.RequestException as e:
            print(f"Error registering charging station: {e}")
            return False

    def get_end_point(self, message_name:str, payload):
        pass

    def request_api(self, end_point, payload):
        pass

    def send_message_end_point(self, message_name, payload):
        normalized_name = message_name.removesuffix("Request")
        if normalized_name == "TriggerMessage" and "requestedMessage" in payload:
            if payload["requestedMessage"] in self.trigger_message_list:
                url = f"{self.api_uri}cs/{self.CS_NAME}/trigger"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "trigger": payload["requestedMessage"]
                }
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    return response.status_code == 200 or response.status_code == 201
                except requests.RequestException as e:
                    print(f"Error registering charging station: {e}")
                    return False
        return False

    def set_evse_id(self, evse_id) -> bool:
        return False

    def set_variables(self, set_variable_data_list):
        pass