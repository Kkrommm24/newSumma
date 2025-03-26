import re
from datetime import datetime, timedelta, timezone

def parse_datetime_manual(datetime_str):
    datetime_clean = re.sub(r'^[^\d]*', '', datetime_str)
    datetime_clean = re.sub(r'\s*\(.*\)', '', datetime_clean)
    dt = datetime.strptime(datetime_clean, "%d/%m/%Y, %H:%M")
    tz = timezone(timedelta(hours=7))
    dt = dt.replace(tzinfo=tz)
    return dt.isoformat()
