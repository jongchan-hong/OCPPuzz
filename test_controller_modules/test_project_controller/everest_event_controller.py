from typing import Optional

from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from test_controller_modules.test_project_controller.project_event_controller import ProjectEventController
import docker
import time
import json
import os


class EverestEventController(ProjectEventController):
    CS_NAME = "CHARGER"
    port = 9100
    socket_uri = f"ws://localhost:{port}/"
    project_name = "Everest"

    def get_restart_container_name_list(self):
        client = docker.from_env()
        return [client.containers.get(self.ws_container_name)]

    def _db_init(self):
        pass

    def coverage_init(self):
        pass

    def get_uri(self) -> str:
        return self.socket_uri + self.CS_NAME

    def get_total_coverage(self)->TotalCoverageDTO:
        self.ws.close()
        client = docker.from_env()
        container = client.containers.get(self.api_container_name)

        print(f"[{self.project_name}] Executing stop_server.sh...")
        exec_result = container.exec_run(cmd="/bin/bash /usr/local/apps/ocpp-csms/stop_server.sh")
        print(exec_result.output.decode())
        time.sleep(2)

        local_path = "./coverage.json"
        container_path = "/usr/local/apps/ocpp-csms/coverage.json"

        print(f"[{self.project_name}] Copying coverage.json from container...")
        try:
            os.remove(local_path)
        except FileNotFoundError:
            pass
        stream, stat = container.get_archive(container_path)
        import tarfile, io
        with tarfile.open(fileobj=io.BytesIO(b''.join(stream)), mode='r|*') as tar:
            for member in tar:
                if member.name.endswith("coverage.json"):
                    with tar.extractfile(member) as f:
                        coverage_data = json.load(f)
                        break
            else:
                raise RuntimeError("coverage.json not found in archive")
        totals = coverage_data.get("totals", {})
        print(f"[{self.project_name}] Restarting server with start_server.sh...")
        container.exec_run(cmd="/bin/bash /usr/local/apps/ocpp-csms/start_server.sh", detach=True)
        time.sleep(3)
        self.connect()
        return TotalCoverageDTO(
            total_statements=totals["num_statements"],
            covered_statements=totals["covered_lines"],
            total_branches=totals["num_branches"],
            covered_branches=totals["covered_branches"],
        )

    def get_project_name(self) -> str:
        return self.project_name

    def dump_coverage_request(self) -> bool:
        return True

    def collect_coverage_total_info(self) -> Optional[CoverageInfoDTO]:
        return None

    def insert_token(self, id_token, type) -> bool:
        return False

    def register_charging_station_info(self) -> bool:
        # Not Need
        return True

    def send_message_end_point(self, message_name, payload) -> bool:
        return False

    def set_evse_id(self, evse_id) -> bool:
        return False

    def set_variables(self, set_variable_data_list):
        pass