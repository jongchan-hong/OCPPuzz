import base64
from sqlalchemy import Table, select, insert
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from test_controller_modules.test_project_controller.ocpp_core_event_controller import OCPPCoreEventController


class AuthMaker():
    def __init__(self):
        self.db_engine = None
        self.metadata = None
        self.project_session = None
        self._db_init()

    def _db_init(self):
        from urllib.parse import quote_plus
        password = quote_plus("YourStrong@Password1!")
        conn_str = f"mssql+pyodbc://SA:{password}@localhost:1433/OCPP.Core?driver=ODBC+Driver+17+for+SQL+Server"
        self.db_engine = create_engine(conn_str)
        self.metadata = MetaData()
        Session = sessionmaker(bind=self.db_engine)
        self.project_session = Session()

    def make(self, cs_name):
        charge_point_table = Table("ChargePoint", self.metadata, autoload_with=self.db_engine)

        with self.db_engine.connect() as conn:
            stmt = select(charge_point_table.c.ChargePointId).where(
                charge_point_table.c.ChargePointId == cs_name)
            if not conn.execute(stmt).first():
                values = {
                    "ChargePointId": cs_name,
                    "Name": cs_name,
                    "Comment": f"Auto-registered {cs_name}",
                    "Username": cs_name,
                    "Password": cs_name,
                    "ClientCertThumb": None
                }

                insert_stmt = insert(charge_point_table).values(values)
                conn.execute(insert_stmt)
                conn.commit()
            credentials = f"{cs_name}:{cs_name}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            print(f"[Header] Authorization: Basic {encoded_credentials}")
            print("[Header] Sec-WebSocket-Protocol: ocpp2.0.1")
            print(OCPPCoreEventController.socket_uri + cs_name)


cs_name = input("Enter your CS Name >>")
maker = AuthMaker()
maker.make(cs_name)