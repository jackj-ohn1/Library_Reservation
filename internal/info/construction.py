import requests

from internal.util.setting import *
from internal.util.util import *
from internal.info.area import AreaInfo


class ConstructionInfo:

    def __init__(self, name: str, session: requests.Session):
        if session is None:
            raise Exception("session can't be None!")

        self.construction = name

        self.__session = session
        self.__area_no: list[str] = [OPEN_FIRST, OPEN_FIRST_MID,
                                     OPEN_SECOND,
                                     OPEN_SECOND_MID]
        self.__areas: dict[str:AreaInfo] = {}

    def __get_area_info(self):
        for no in self.__area_no:
            area = AreaInfo(no, self.__session)
            area.get_reservation_info()

            self.__areas[area.class_name] = area

    def __clear_reservation(self):
        self.__areas.clear()

    def __refresh_session(self, session: requests.Session):
        self.__session = None
        self.__session = session

    def show_target_area_reservation(self, class_name="", useful: int = 10):
        if class_name not in self.__areas.keys():
            print("this class_name is not exist.")
            return

        self.__areas[class_name].show_useful_reservation(useful)

    def show_all_area_reservation(self, useful: int = 10):
        for key, val in self.__areas.items():
            val.show_useful_reservation(useful)
            print()

    def show_area_with_spare(self, *class_no, gap: int = 30, show: bool = True):
        for val in class_no:
            if val in REFLECT_NAME.keys():
                self.__areas[REFLECT_NAME[val]].get_spare_time(gap, show)
            else:
                print("please input the useful parameter!")

    def flush_reservation(self, session: requests.Session):
        self.__refresh_session(session)
        self.__clear_reservation()
        self.__get_area_info()

    def prepare(self):
        self.__get_area_info()
        self.show_area_with_spare(OPEN_SECOND_MID,OPEN_SECOND,OPEN_FIRST,OPEN_FIRST_MID,show=False)

    def find_seat(self, start: str, end: str, priority: list):
        if start == '' or end == 'str':
            raise Exception("time can't be empty!")

        max_length = 0
        max_slot = None
        seat_no = ''
        room_name = ''
        dev_id = ''
        ret: dict = {}
        storage_child: list = []

        if not compare_with_word(get_time(), start, 0):
            start = get_time()

        for i in priority:
            if i not in REFLECT_NAME.keys() or REFLECT_NAME[i] not in self.__areas.keys():
                raise Exception('the ele in list must is useful!')

            not_successful: dict = {}
            for seat in self.__areas[REFLECT_NAME[i]].seat_info:
                for spare_time in seat.spare_time:
                    start_l, start_r = map(int, str(spare_time[0]).split(':'))
                    end_l, end_r = map(int, str(spare_time[1]).split(':'))
                    length = end_l * 60 - start_l * 60 + end_r - start_r

                    if max_slot is not None and spare_time[0] < max_slot[0] and spare_time[1] > max_slot[
                        1] and length > max_length:
                        max_length = length

                        max_slot = (spare_time[0], spare_time[1])
                        seat_no = seat.seat_no
                        room_name = seat.room_name
                        dev_id = seat.dev_id

                        not_successful['duration'] = max_slot
                        not_successful['seat'] = seat_no
                        not_successful['room_name'] = room_name
                        not_successful['dev_id'] = dev_id

                    if spare_time[0] <= start and spare_time[1] >= end:
                        if length > max_length:
                            max_length = length

                        ret['duration'] = (spare_time[0], spare_time[1])
                        ret['seat'] = seat.seat_no
                        ret['room_name'] = seat.room_name
                        ret['dev_id'] = seat.dev_id
                        ret['not_successful'] = []

                        return ret

            storage_child.append(not_successful)

        ret['duration'] = ''
        ret['seat'] = seat_no
        ret['room_name'] = room_name
        ret['dev_id'] = dev_id
        ret['not_successful'] = storage_child

        return ret
