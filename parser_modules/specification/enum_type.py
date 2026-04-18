from parser_modules.parser_util import is_value_point
from constants.parse_mode import ParseMode
from typing import List

class EnumMember:
    def __init__(self, row: List[str]):
        self.value = row[0].replace("\n", "")
        self.description = row[1].replace("\n", " ")
    def get_information(self):
        result = {}
        result["name"] = self.value
        result["field_description"] = self.description
        return result


class EnumType:
    def __init__(self, name, description, field_tables):
        self.name = name
        self.description = description
        self.field_tables = field_tables
        self.enum_members: List[EnumMember] = []
        for table in self.field_tables:
            rows = table.extract()
            for row in rows:
                if row[0] == "Value":
                    continue
                enum_member = EnumMember(row)
                self.enum_members.append(enum_member)
    def get_information(self, parser):
        result = {}
        result['enumMembers'] = []
        for enum_member in self.enum_members:
            result['enumMembers'].append(enum_member.get_information())
        return result




def get_enumerations_from_pages(version, pages, config):
    enumerations = []
    parse_mode = ParseMode.READ_MODE
    save_tables = set()
    current_description = ""
    current_enumerations = None

    for index, page in enumerate(pages):
        y_min = 0
        text = page.extract_text()
        if not text:
            continue
        words = page.extract_words()
        tables = page.find_tables()

        for word in words:
            if 819 < word["top"] < 820 or word["top"] < 11.44:
                continue
            if round(word["height"]) == config["size"]["level_2_height"]:
                if word["text"].endswith("EnumType"):
                    if current_enumerations:
                        if y_min == 0:
                            for table in tables:
                                if table.bbox[1] < word["top"]:
                                    save_tables.add(table)
                                    break
                        enumerations.append(EnumType(current_enumerations, current_description.strip(), save_tables))
                        save_tables = set()
                        current_description = ""
                    current_enumerations = word["text"]
                    parse_mode = ParseMode.DESCRIPTION_COLLECT_MODE
                    y_min = word["top"]
                else:
                    continue
            elif parse_mode == ParseMode.DESCRIPTION_COLLECT_MODE:
                if is_enumeration_point(config, word):
                    continue
                elif is_value_point(config, word):
                    for table in tables:
                        if table.bbox[1] > y_min:
                            save_tables.add(table)
                            break
                    parse_mode = ParseMode.READ_MODE
                else:
                    current_description += word["text"] + " "
        if index == len(pages) - 1 and current_enumerations:
            enumerations.append(EnumType(current_enumerations, current_description.strip(), save_tables))
    return enumerations

def is_enumeration_point(config, word):
    return word["text"] == "Enumeration" and round(word["x0"]) == config["coordinate"]["class_x"]