import random
import string

class HTML:
    html_tags = ['b', 'i', 'u', 'div', 'span', 'a', 'p', 'strong', 'em']
    html_entities = ['&nbsp;', '&lt;', '&gt;', '&amp;', '&quot;', '&#169;', '&#174;']
    MIN_LENGTH_LIMIT = 71
    @staticmethod
    def generate(length: int) -> str:
        result = ""
        while len(result) < length:
            choice = random.choice(['tag', 'entity', 'text'])

            if choice == 'tag':
                tag = random.choice(HTML.html_tags)
                inner = ''.join(random.choices(string.ascii_letters, k=random.randint(1, 3)))
                tag_str = f"<{tag}>{inner}</{tag}>"
            elif choice == 'entity':
                tag_str = random.choice(HTML.html_entities)
            else:
                tag_str = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 5)))

            if len(result) + len(tag_str) > length:
                tag_str = tag_str[:length - len(result)]
            result += tag_str
        return result

    @staticmethod
    def generate_fixed_length_html(length: int) -> str:
        template_prefix = "<!DOCTYPE html><html><head><title>R</title></head><body>"
        template_suffix = "</body></html>"

        base_len = len(template_prefix) + len(template_suffix)
        if length <= base_len:
            raise ValueError(f"min length: {base_len + 1}  (now: {length})")

        content_len = length - base_len
        content = HTML.generate(content_len)
        return f"{template_prefix}{content}{template_suffix}"