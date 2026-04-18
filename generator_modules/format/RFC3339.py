import datetime
import random
from datetime import datetime, timedelta, timezone
class RFC3339:
    @staticmethod
    def random_generate(decimal_places_max):
        random_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 3650),
                                                             hours=random.randint(0, 23),
                                                             minutes=random.randint(0, 59),
                                                             seconds=random.randint(0, 59),
                                                             microseconds=random.randint(0, 999999))

        if decimal_places_max > 0:
            fractional_seconds = int(random_date.microsecond // (10 ** (6 - decimal_places_max)))
            fractional_part = f".{fractional_seconds:0{decimal_places_max}d}"
        else:
            fractional_part = ""

        if random.choice([True, False]):
            return f"{random_date.strftime('%Y-%m-%dT%H:%M:%S')}{fractional_part}Z"
        else:
            offset_hours = random.randint(-12, 14)
            offset_minutes = random.choice([0, 15, 30, 45])
            offset_sign = "+" if offset_hours >= 0 else "-"
            offset_str = f"{offset_sign}{abs(offset_hours):02}:{offset_minutes:02}"
            random_date = random_date.astimezone(timezone(timedelta(hours=offset_hours, minutes=offset_minutes)))
            return f"{random_date.strftime('%Y-%m-%dT%H:%M:%S')}{fractional_part}{offset_str}"