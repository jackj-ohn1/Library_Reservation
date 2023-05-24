import time

import orjson
import requests
from internal.info.seat import SeatInfo
from internal.util.util import *



class AreaInfo:
    def __init__(self, class_no, session: requests.Session):
        if session is None:
            raise Exception("identification can't be None!")
        self.__session = session
        self.__LIBRARY_DATA_URL = "http://kjyy.ccnu.edu.cn/ClientWeb/pro/ajax/device.aspx"

        self.class_no = class_no
        self.class_name = ""
        self.seat_info: list[SeatInfo] = []
        self.__open_start, self.__open_end = "", ""

        self.__show_params = {
            "byType": "devcls", "classkind": 8, "display": "fp",
            "md": "d", "cld_name": "default", "act": "get_rsv_sta",
            "date": "", "fr_start": "", "fr_end": "22:00", "_": "",
            "room_id": class_no,
        }
        self.__headers = {
            "Host": "kjyy.ccnu.edu.cn",
        }

    def header_add(self, key, val):
        if key in self.__headers.keys():
            raise Exception("the key exists, please use header_set()")
        self.__headers[key] = val

    def header_set(self, key, val):
        self.__headers[key] = val

    def header_del(self, key):
        self.__headers.pop(key)

    def get_reservation_info(self):
        self.__show_params["_"] = str(int(round(time.time() * 1000)))
        self.__show_params["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.__show_params["fr_start"] = str(get_time())

        resp = self.__session.get(url=self.__LIBRARY_DATA_URL, params=self.__show_params, headers=self.__headers)
        reservation: dict = orjson.loads(resp.text)
        for one in reservation["data"]:
            if self.class_name == "":
                self.class_name = one["roomName"]

            if self.__open_start == "" or self.__open_end == "":
                self.__open_start = one["open"][0]
                self.__open_end = one["open"][1]

            self.seat_info.append(SeatInfo(one))

    def show_useful_reservation(self, useful: int):
        print(f"this is in {self.class_name}:")
        count = 0
        for i in range(0, len(self.seat_info)):
            if useful > 0:
                if count >= useful:
                    return

            if self.seat_info[i].get_length() <= 0:
                continue

            self.seat_info[i].show_seat_info()
            count += 1

    def show_reservation(self, num: int):
        print(f"this is in {self.class_name}:")
        count = 0
        for i in range(0, len(self.seat_info)):
            if num > 0:
                if count >= num:
                    return

            self.seat_info[i].show_seat_info()
            count += 1

    def show_arrange_time(self):
        print(f"{self.__open_start} begin! {self.__open_end} over!")

    def get_spare_time(self, gap: int, show: bool):
        for one in self.seat_info:
            one.get_spare_time(self.__open_start, self.__open_end, gap, show)