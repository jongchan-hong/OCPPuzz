from constants.ocpp_version import OcppVersion

class PrimitiveDataType:
    def __init__(self, data_type, description):
        self.data_type = data_type
        self.description = description

    def get_information(self):
        result = {}
        result["name"] = self.data_type
        result["field_description"] = self.description
        return result

def get_primitive_data_types_from_pages(version, pages, config):
    if version == OcppVersion.version_160:
        return None
    data_types = []
    save_tables = set()

    for index, page in enumerate(pages):
        y_min = 0
        text = page.extract_text()
        if not text:
            continue
        tables = page.find_tables()
        for table in tables:
            rows = table.extract()
            for row in rows:
                if row[0] == "Datatype":
                    continue
                data_types.append(PrimitiveDataType(row[0], row[1]))
    return data_types
