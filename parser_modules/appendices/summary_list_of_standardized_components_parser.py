from typing import List

from pdfplumber.page import Page
from parser_modules.appendices.standardized_component import StandardizedComponent

class SummaryListOfStandardizedComponentsParser:
    def __init__(self, pages:List[Page]):
        self.pages = pages
        self.list:List[StandardizedComponent] = self.collect_components()

    def collect_components(self) -> List[StandardizedComponent]:
        result = []
        for index, page in enumerate(self.pages):
            for table in page.find_tables():
                rows = table.extract()
                for row in rows:
                    if row[0] == "Component" and row[1] == "Description":
                        continue
                    result.append(StandardizedComponent(
                        name = row[0],
                        description = row[1],
                    ))
        return result

    def get_name_list(self) -> List[str]:
        return [standardized_component.name for standardized_component in self.list]