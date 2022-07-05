from datetime import datetime


def change_date_format(date_to_modify):
    temp_date = date_to_modify
    temp_time = datetime.min.time()

    return datetime.combine(temp_date, temp_time)