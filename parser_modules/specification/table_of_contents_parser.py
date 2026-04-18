from typing import List

from pdfplumber.page import Page

from dto.constraint_collect_dto import PageRange
from parser_modules.appendices.standardized_measure import StandardizedMeasure
from typing import List, Dict, Optional
from pdfplumber.page import Page
from collections import defaultdict
import re, json

class TableOfContentsParser:
    def __init__(self, pages: List[Page], config: Dict):
        self.pages = pages
        self.config = config
        self.tree = self.collect()
    def get_page_index(self, page_range: PageRange):
        return 5,5

    def get_instruction_content(self):
        return json.dumps(self.tree, ensure_ascii=False)
    def collect(self):
        result = []
        toc_config = self.config["table_of_contents"]
        left_tab = toc_config["left_tab"]
        page_number_x0 = toc_config["page_number_x0"]
        tolerance = 1.5

        for page_index, page in enumerate(self.pages):
            words = page.extract_words()
            lines = {}
            for word in words:
                line_y = round(word["top"], 1)
                lines.setdefault(line_y, []).append(word)

            for line_words in lines.values():
                line_words.sort(key=lambda w: w["x0"])
                line_text = ""
                level = None
                page_number = None

                for word in line_words:
                    x0 = word["x0"]
                    text = word["text"].strip()

                    if x0 >= page_number_x0 - tolerance and text.isdigit():
                        page_number = int(text)
                        continue

                    if re.fullmatch(r"[.·•]+", text):
                        continue

                    for lvl, lvl_x0 in left_tab.items():
                        if abs(x0 - lvl_x0) < tolerance:
                            if not level or left_tab[lvl] < left_tab[level]:
                                level = lvl
                            break

                    line_text += text + " "

                title_cleaned = line_text.strip().rstrip(".").strip()
                if title_cleaned and page_number is not None:
                    result.append({
                        "title": title_cleaned,
                        "level": level,
                        "page": page_number
                    })

        level_priority = {lvl: i for i, lvl in enumerate(sorted(left_tab, key=lambda l: left_tab[l]))}
        root = []
        stack = []

        for item in result:
            node = {
                "title": item["title"],
                "page": item["page"],
                "children": []
            }
            current_level = level_priority[item["level"]]

            while stack and level_priority[stack[-1][1]] >= current_level:
                stack.pop()

            if not stack:
                root.append(node)
            else:
                stack[-1][0]["children"].append(node)

            stack.append((node, item["level"]))

        return root


