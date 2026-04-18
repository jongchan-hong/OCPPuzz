
from parser_modules.parser_util import is_class_point, is_field_point
from constants.parse_mode import ParseMode
from parser_modules.specification.object import Object


class DataType(Object):
    def __init__(self, name, description, field_tables):
        super().__init__(name, description, field_tables)

def get_data_types_from_pages(version, pages, config):
    data_types = []
    parse_mode = ParseMode.READ_MODE
    save_tables = set()
    current_description = ""
    current_data_type = None

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
                if word["text"].endswith("Type") or word["text"].endswith("Data"):
                    if current_data_type:
                        if y_min == 0:
                            for table in tables:
                                if table.bbox[1] < word["top"]:
                                    save_tables.add(table)
                                    break
                        data_types.append(DataType(current_data_type, current_description.strip(), save_tables))
                        save_tables = set()
                        current_description = ""
                    current_data_type = word["text"]
                    parse_mode = ParseMode.DESCRIPTION_COLLECT_MODE
                    y_min = word["top"]
                else:
                    continue
            elif parse_mode == ParseMode.DESCRIPTION_COLLECT_MODE:
                if is_class_point(config, word):
                    continue
                elif is_field_point(config, word):
                    for table in tables:
                        if table.bbox[1] > y_min:
                            save_tables.add(table)
                            break
                    parse_mode = ParseMode.READ_MODE
                else:
                    current_description += word["text"] + " "
        if index == len(pages) - 1 and current_data_type:
            data_types.append(DataType(current_data_type, current_description.strip(), save_tables))
    return data_types