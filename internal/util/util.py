import datetime


def compare_with_word(start: str, end: str, gap: int):
    start_split, end_split = start.split(":"), end.split(":")

    start_l, start_r = int(start_split[0]), int(start_split[1])
    end_l, end_r = int(end_split[0]), int(end_split[1])

    if start_l >= end_l:
        return ""
    elif start_l <= end_l:
        if (end_l - start_l) * 60 + (end_r - start_r) > gap:
            return True

    # start + gap > end
    # start is after end
    return False


def get_time():
    now = datetime.datetime.now()
    return now.strftime('%H:%M')


def get_date():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')
