from constants.ocpp_version import OcppVersion

class Config:
    def __init__(self, document_path, config_path, version, json_schema_folder_path, appendices_document_path = None):
        self.document_path = document_path
        self.config_path = config_path
        self.version = version
        self.json_schema_folder_path = json_schema_folder_path
        self.appendices_document_path = appendices_document_path
    def get_schema_path(self, message_name:str):
        return self.json_schema_folder_path +"/"+ message_name+".json"

version160 = Config(
    "documents/1.6/ocpp-1.6 edition 2.pdf",
    "version_conf/160.conf.yaml",
    OcppVersion.version_160,
    "documents/1.6/json"
)

version201 = Config(
    "documents/2.0.1/OCPP-2.0.1_edition3_part2_specification.pdf",
"version_conf/201.conf.yaml",
OcppVersion.version_201,
"documents/2.0.1/json",
    "documents/2.0.1/OCPP-2.0.1_edition3_part2_appendices_v14.pdf"
)

version210 = Config(
    "documents/2.1/OCPP-2.1_edition1_part2_specification.pdf",
"version_conf/210.conf.yaml",
OcppVersion.version_210,
"documents/2.1/json"
)