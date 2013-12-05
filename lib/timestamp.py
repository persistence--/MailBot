from datetime import datetime


# Returns a human readable timestamp string: YYYY-MM-DD hh:mm:ss
def timestamp():
    timestamp = "%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d" % {
                "year": datetime.now().year,
                "month": datetime.now().month,
                "day": datetime.now().day,
                "hour": datetime.now().hour,
                "minute": datetime.now().minute,
                "second": datetime.now().second, }
    return timestamp   