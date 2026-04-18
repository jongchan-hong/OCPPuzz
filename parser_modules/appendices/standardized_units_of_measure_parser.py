from typing import List

from pdfplumber.page import Page
from parser_modules.appendices.standardized_measure import StandardizedMeasure

class StandardizedUnitsOfMeasureParser:
    def __init__(self, pages:List[Page]):
        self.pages = pages
        self.list:List[StandardizedMeasure] = self.collect()

    def collect(self) -> List[StandardizedMeasure]:
        result = []
        for index, page in enumerate(self.pages):
            tables = page.find_tables()
            for table in tables:
                rows = table.extract()
                for row in rows:
                    if self.is_header(row):
                        continue
                    result.append(StandardizedMeasure(
                        name = row[0],
                        description=row[1]
                    ))
        return result

    def is_header(self, row):
        return row[0] == "Value" and row[1] == "Description"

    def get_name_list(self) -> List[str]:
        return [standardized_measure.name for standardized_measure in self.list]