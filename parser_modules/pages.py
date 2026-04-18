import pdfplumber
from constants.parse_type import ParseType
import yaml
import re

from dto.scenario_page_dto import ScenarioPageDTO


class Pages:
    def __init__(self, config, yaml_config):
        self.config = config
        self.yaml_config = yaml_config
        self.__messages = []
        self.__data_types = []
        self.__enumerations = []
        self.__primitive_data_types = []
        self.__variables = []
        self.__table_of_contents = []
        self.__page_index = {}

        with pdfplumber.open(config.document_path) as pdf:
            parse_type = ParseType.NOTING
            for index, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    for line_index, line in enumerate(lines):
                        for data in yaml_config["group"]:
                            if "end_signature" in data and line == data["end_signature"]:
                                parse_type = ParseType.NOTING
                            if line == data["start_signature"]:
                                parse_type = ParseType(data["parse_type"])
                        if line_index == len(lines)-1:
                            match = re.search(r'\b(\d+)/\d+\b', line)
                            if match:
                                page_number = match.group(1)
                                self.__page_index[int(page_number)] = index
                match parse_type:
                    case ParseType.MESSAGES:
                        self.__messages.append(page)
                    case ParseType.DATA_TYPES:
                        self.__data_types.append(page)
                    case ParseType.ENUMERATIONS:
                        self.__enumerations.append(page)
                    case ParseType.PRIMITIVE_DATA_TYPES:
                        self.__primitive_data_types.append(page)
                    case ParseType.VARIABLES:
                        self.__variables.append(page)
                    case ParseType.TABLE_OF_CONTENTS:
                        self.__table_of_contents.append(page)

        print("__Messages size : " + str(len(self.__messages)))
        print("__DataTypes size : " + str(len(self.__data_types)))
        print("__Enumerations size : " + str(len(self.__enumerations)))
        print("__primitive_data_types size : " + str(len(self.__primitive_data_types)))
        print("__variables size : " + str(len(self.__variables)))
        print("__table_of_contents size : " + str(len(self.__table_of_contents)))
    def get_primitive_data_types_pages(self):
        return self.__primitive_data_types
    def get_message_pages(self):
        return self.__messages
    def get_data_types_pages(self):
        return self.__data_types
    def get_enumerations_pages(self):
        return self.__enumerations
    def get_variables_pages(self):
        return self.__variables
    def get_table_of_contents_pages(self):
        return self.__table_of_contents
    def get_page_index(self, page_number):
        return self.__page_index[page_number]
    def get_page_number(self, index: int) -> int:
        inverse_index = {v: k for k, v in self.__page_index.items()}
        return inverse_index[index]

    def get_scenario_pages(self):
        class ScenarioFindException(Exception):
            def __init__(self, name: str, type_value: str):
                super().__init__(name)
                self.message = name
                self.type_value = type_value

        result = []

        with pdfplumber.open(self.config.document_path) as pdf:
            scenario_name = ""
            for index, page in enumerate(pdf.pages):
                tables = page.find_tables()
                for table in tables:
                    rows = table.extract()
                    try:
                        for row in rows:
                            if len(row) == 3 and row[1] is not None:
                                type_value = re.sub(r'\s+', ' ', row[1]).replace("\n", " ").lower()
                                match type_value:
                                    case "name":
                                        if row[2] and row[2].strip():
                                            scenario_name = row[2]
                                    case _:
                                        if "scenario description" in type_value:
                                            if "alternative" not in type_value and "combined" not in type_value:
                                                raise ScenarioFindException(scenario_name, type_value)
                    except ScenarioFindException as e:
                        figure_page_index, figure_line  = self.get_figure_line_texts(index, pdf.pages, table.bbox[1])
                        result.append(
                            ScenarioPageDTO(
                                scenario_name= e.message,
                                start_index= index,
                                end_index= figure_page_index,
                                figure_line = figure_line
                            )
                        )
        return result

    def get_figure_line_texts(self, start_index, pages, table_y):
        for i in range(start_index, len(pages)):
            words = pages[i].extract_words()
            for word in words:
                if round(word["x0"]) == self.yaml_config["figure"]["x"] and word["text"].lower() == "figure":
                    line_top = float(word["top"])
                    if i == start_index and line_top <= table_y:
                        continue

                    line_words = [
                        w for w in words if abs(float(w["top"]) - line_top) <= 2.0
                    ]

                    line_text = " ".join(w["text"] for w in sorted(line_words, key=lambda w: w["x0"]))
                    return i, line_text
        return None, None
