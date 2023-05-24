import requests
from internal.info.construction import ConstructionInfo

Construction_Outer: ConstructionInfo = None


def get_construction_info(session: requests.Session):
    global Construction_Outer
    flush_construction_info(session)
    Construction_Outer.prepare()
    return Construction_Outer


def flush_construction_info(session: requests.Session):
    global Construction_Outer
    if session is None:
        raise Exception("identification can't be None!")
    if Construction_Outer is None:
        Construction_Outer = ConstructionInfo("南湖综合楼", session)
    Construction_Outer.flush_reservation(session)


