from typing import Optional

from dto.coverage_info_dto import CoverageInfoDTO
from dto.total_coverage_dto import TotalCoverageDTO
from test_controller_modules.test_project_controller.project_event_controller import ProjectEventController
import docker
import time


class OCPPGoController(ProjectEventController):
    CS_NAME = "CHARGER"
    socket_port = 8887
    socket_uri = f"ws://localhost:{socket_port}/"
    project_name = "ocpp-go"

    def get_restart_container_name_list(self):
        client = docker.from_env()
        return [client.containers.get(self.ws_container_name)]

    def _db_init(self):
        pass

    def coverage_init(self):
        pass

    def get_total_coverage(self)->TotalCoverageDTO:
        self.ws.close()
        client = docker.from_env()
        socket_container = self.get_container_name_by_port(self.socket_port)
        container = client.containers.get(socket_container)
        container.exec_run(cmd="/go/src/github.com/lorenzodonini/ocpp-go/stop_server.sh")
        print(f"[{self.project_name}] Executing stop_server.sh...")
        time.sleep(2)
        container_path = "/go/src/github.com/lorenzodonini/ocpp-go/coverage.out"

        print(f"[{self.project_name}] Copying coverage.out from container...")
        stream, stat = container.get_archive(container_path)
        import tarfile, io
        container.exec_run(cmd="/bin/bash /go/src/github.com/lorenzodonini/ocpp-go/start_server.sh", detach=True)
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

    def get_uri(self) -> str:
        return self.socket_uri + self.CS_NAME

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