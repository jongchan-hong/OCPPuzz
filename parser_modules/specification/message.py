
from parser_modules.parser_util import is_class_point
from constants.ocpp_version import OcppVersion
from constants.parse_mode import ParseMode
from parser_modules.specification.object import Object
from parser_modules.specification.pettern import level_2_pattern


class Message(Object):
    def __init__(self, name, description, field_tables):
        super().__init__(name, description, field_tables)

def get_message_from_pages_160(pages, config):
    messages = []
    parse_mode = ParseMode.READ_MODE
    save_tables = set()
    current_description = ""
    current_message = None

    for index, page in enumerate(pages):
        y_min = 0
        text = page.extract_text()
        if not text:
            continue
        words = page.extract_words()
        tables = page.find_tables()
        for word in words:
            if round(word["bottom"]) == 831:
                continue
            if round(word["height"]) == config["size"]["level_2_height"] and (
                    word["text"].endswith(".req") or word["text"].endswith(".conf")):
                if current_message:
                    if y_min == 0:
                        for table in tables:
                            if table.bbox[1] < word["top"]:
                                save_tables.add(table)
                                break
                    messages.append(Message(current_message, current_description.strip(), save_tables))
                    save_tables = set()
                    current_description = ""
                current_message = word["text"]
                parse_mode = ParseMode.DESCRIPTION_COLLECT_MODE
                y_min = word["top"]
            elif parse_mode == ParseMode.DESCRIPTION_COLLECT_MODE:
                if word["text"] == "FIELD" and round(word["x0"]) == config["coordinate"]["field_x0"]:
                    for table in tables:
                        if table.bbox[1] > y_min:
                            save_tables.add(table)
                            break
                    parse_mode = ParseMode.READ_MODE
                elif word["height"] != config["size"]["level_2_height"]:
                    current_description += word["text"] + " "
        if index == len(pages) - 1 and current_message:
            messages.append(Message(current_message, current_description.strip(), save_tables))
    return messages

def get_message_from_pages(version, pages, config):
    if version == OcppVersion.version_160:
        return get_message_from_pages_160(pages, config)
    messages = []
    parse_mode = ParseMode.READ_MODE
    save_tables = set()
    current_description = ""
    current_message = None

    for index, page in enumerate(pages):
        y_min = 0
        text = page.extract_text()
        if not text:
            continue
        words = page.extract_words()
        tables = page.find_tables()

        for word in words:
            if 819<word["top"]<820 or word["top"]<11.44:
                continue
            if (round(word["height"]) == config["size"]["level_2_height"] and level_2_pattern.match(word["text"])):
                parse_mode = ParseMode.READ_MODE
            if round(word["height"]) == config["size"]["level_3_height"]:
                if word["text"].endswith("Request") or word["text"].endswith("Response"):
                    if current_message:
                        if y_min == 0:
                            for table in tables:
                                if table.bbox[1] < word["top"]:
                                    save_tables.add(table)
                                    break
                        messages.append(Message(current_message, current_description.strip(), save_tables))
                        save_tables = set()
                        current_description = ""
                    current_message = word["text"]
                    parse_mode = ParseMode.DESCRIPTION_COLLECT_MODE
                    y_min = word["top"]
                else:
                    continue
            elif parse_mode == ParseMode.DESCRIPTION_COLLECT_MODE:
                if is_class_point(config, word):
                    for table in tables:
                        if table.bbox[1] > y_min:
                            save_tables.add(table)
                            break
                    parse_mode = ParseMode.READ_MODE
                else:
                    current_description += word["text"] + " "
        if index == len(pages) - 1 and current_message:
            messages.append(Message(current_message, current_description.strip(), save_tables))
    return messages
