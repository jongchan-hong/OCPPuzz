import pdfplumber

from constants.appendices_parse_type import AppendicesParseType
import re
class AppendicesPages:
    def __init__(self, config, yaml_config):
        self.__security_events = []
        self.__standardized_units_of_measure = []
        self.__summary_list_of_standardized_components = []
        self.__standardized_variables = []
        self.__table_of_contents = []
        self.__page_index = {}

        with pdfplumber.open(config.appendices_document_path) as pdf:
            parse_type = AppendicesParseType.NOTING
            end_signature = None
            for index, page in enumerate(pdf.pages):
                text = page.extract_text()

                if text:
                    lines = text.split("\n")
                    for line_index, line in enumerate(lines):
                        if line_index == len(lines)-1:
                            match = re.search(r'\b(\d+)/\d+\b', line)
                            if match:
                                page_number = match.group(1)
                                self.__page_index[int(page_number)] = index
                        for data in yaml_config["appendices_group"]:
                            if end_signature and line == end_signature:
                                parse_type = AppendicesParseType.NOTING
                                end_signature = None
                            if line == data["start_signature"]:
                                parse_type = AppendicesParseType(data["parse_type"])
                                end_signature = data["end_signature"]
                                break
                match parse_type:
                    case AppendicesParseType.SECURITY_EVENTS:
                        self.__security_events.append(page)
                    case AppendicesParseType.STANDARDIZED_UNITS_OF_MEASURE:
                        self.__standardized_units_of_measure.append(page)
                    case AppendicesParseType.SUMMARY_LIST_OF_STANDARDIZED_COMPONENTS:
                        self.__summary_list_of_standardized_components.append(page)
                    case AppendicesParseType.STANDARDIZED_VARIABLES:
                        self.__standardized_variables.append(page)
                    case AppendicesParseType.TABLE_OF_CONTENTS:
                        self.__table_of_contents.append(page)

        print("__security_events size : " + str(len(self.__security_events)))
        print("__standardized_units_of_measure size : " + str(len(self.__standardized_units_of_measure)))
        print("__summary_list_of_standardized_components size : " + str(len(self.__summary_list_of_standardized_components)))
        print("__standardized_variables size : " + str(len(self.__standardized_variables)))

    def get_security_events_pages(self):
        return self.__security_events
    def get_standardized_units_of_measure_pages(self):
        return self.__standardized_units_of_measure
    def get_summary_list_of_standardized_components_pages(self):
        return self.__summary_list_of_standardized_components
    def get_standardized_variables_pages(self):
        return self.__standardized_variables
    def get_table_of_contents_pages(self):
        return self.__table_of_contents
    def get_page_index(self, page_number):
        return self.__page_index[page_number]
    def get_page_number(self, index: int) -> int:
        inverse_index = {v: k for k, v in self.__page_index.items()}
        return inverse_index[index]