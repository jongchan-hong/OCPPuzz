from typing import List

from pdfplumber.page import Page

from parser_modules.appendices.security_event import SecurityEvent

class SecurityEventsParser:
    def __init__(self, pages:List[Page]):
        self.pages = pages
        self.list:List[SecurityEvent] = self.collect_events()

    def collect_events(self) -> List[SecurityEvent]:
        result = []
        for index, page in enumerate(self.pages):
            tables = page.find_tables()
            for table in tables:
                rows = table.extract()
                for row in rows:
                    if self.is_header(row):
                        continue
                    result.append(SecurityEvent(
                        name = row[0],
                        description=row[1],
                        critical=row[2])
                    )
        return result

    def is_header(self, row):
        return row[0] == "Security Event" and row[1] == "Description" and row[2] == "Critical"

    def get_name_list(self) -> List[str]:
        return [security_event.name for security_event in self.list]