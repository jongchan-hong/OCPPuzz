from typing import List, Optional

from pdfplumber.page import Page

from dto.scenario_collect_dto import ConfigurationVariableDTO
from parser_modules.appendices.standardized_variable import StandardizedVariable

class StandardizedVariablesParser:
    def __init__(self, pages:List[Page]):
        self.pages = pages
        self.list:List[StandardizedVariable] = self.collect_variables()

    def collect_variables(self) -> List[StandardizedVariable]:
        result = []
        for index, page in enumerate(self.pages):
            for table in page.find_tables():
                rows = table.extract()
                for row in rows:
                    if self.is_header(row):
                        continue
                    result.append(StandardizedVariable(
                        name = row[0],
                        data_type = row[1],
                        unit=row[2],
                        description=row[3]
                    ))
        return result

    def is_header(self, row):
        return row[0] == "Name" and row[1] == "DataType" and row[2] == "Unit" and row[3] == "Description"

    def get_name_list(self) -> List[str]:
        return [standardized_variable.name for standardized_variable in self.list]