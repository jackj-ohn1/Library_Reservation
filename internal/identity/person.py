# coding:utf-8
import re
import time
from http import cookiejar

import orjson
import requests
from bs4 import BeautifulSoup
from internal.action.reserve import Reservation
from internal.info.function import get_construction_info, flush_construction_info


class PersonInfo:
    BASE_URL = "https://account.ccnu.edu.cn"
    LOGIN_URL = "https://account.ccnu.edu.cn/cas/login"
    LIBRARY_URL = "http://kjyy.ccnu.edu.cn/clientweb/xcus/ic2/Default.aspx"

    HISTORY_URL = 'http://kjyy.ccnu.edu.cn/ClientWeb/pro/ajax/center.aspx'

    def __init__(self, username, password) :
        if username == "" or password == "":
            raise Exception("the two parameter username and password can't be empty.")
        self.__next_url = ""
        self.__lt = ""
        self.__execution = ""
        self.__username = username
        self.__password = password
        self.__session: requests.Session = None

        self.__resv_param = {
            'act': 'get_History_resv', 'strat': '90',
            'StatFlag': 'New', '_': ""
        }

        self.__reservation: dict[dict[str, str]] = {}

        self.__action_reservation: Reservation = None
        self.__priority:list[str] = []

    def __get_params(self):
        res = requests.get(PersonInfo.LOGIN_URL)
        soup = BeautifulSoup(res.text, "html.parser")
        form = soup.find("form", id="fm1")
        self.__next_url = form.attrs["action"]
        self.__lt = form.find(name="input", attrs={"name": "lt"}).attrs["value"]
        self.__execution = form.find(name="input", attrs={"name": "execution"}).attrs["value"]

    def __send_request(self):
        self.__session = requests.session()

        self.__session.cookies = cookiejar.CookieJar()
        self.__session.post(PersonInfo.BASE_URL + self.__next_url, data={"lt": self.__lt,
                                                                         "execution": self.__execution,
                                                                         "username": self.__username,
                                                                         "password": self.__password,
                                                                         "_eventId": "submit",
                                                                         })
        self.__session.get(PersonInfo.LIBRARY_URL)

    def __init_resv_params(self):
        self.__resv_param["_"] = str(int(round(time.time() * 1000)))

    def __capture_rsv_id(self, data: str):
        __soup = BeautifulSoup(data, "html.parser")
        for i in __soup.children:
            __rsv_id_list_rsvId = re.findall(r"rsvId='(.*?)'", data)
            __rsv_id_list_re = re.findall(r'\((.*?)\)', data)
            if len(__rsv_id_list_re) <= 0 and len(__rsv_id_list_rsvId) <= 0:
                continue
            elif len(__rsv_id_list_re) <= 0 and len(__rsv_id_list_rsvId) > 0:
                __rsv_id = __rsv_id_list_rsvId[0]
            elif len(__rsv_id_list_re) > 0 and len(__rsv_id_list_rsvId) <= 0:
                __rsv_id = __rsv_id_list_re[0]
            else:
                __rsv_id = __rsv_id_list_rsvId[0]

            __time = i.find_all_next(name="span", attrs={"class": "text-primary"})
            if len(__time) != 2:
                continue

            self.__reservation[__rsv_id] = {'seat': i.find_next(name="a", attrs={}).text,
                                            'start': __time[0].text,
                                            'end': __time[1].text,
                                            'status': 'not'}

    def __check_identification(self):
        if self.__session is not None:
            return
        self.__get_params()
        self.__send_request()

    # 获取个人的预约
    def __get_reservations(self):
        if self.__session is None:
            raise Exception("please login before get reservation!")
        self.__init_resv_params()

        if len(self.__reservation) > 0:
            self.__reservation.clear()

        resp = self.__session.get(url=PersonInfo.HISTORY_URL, params=self.__resv_param)

        # 133544198
        data = orjson.loads(resp.text)['msg']
        self.__capture_rsv_id(data)

    # 显示个人预约
    def show_reservation(self):
        self.__reservation.clear()
        self.__get_reservations()
        print(f"{self.__username} this is your reservations:")
        for key, val in self.__reservation.items():
            print(f"\t rsv_id:{key} - seat:{val['seat']}\tfrom {val['start']} to {val['end']}")

    def cancel_reservation(self, id: str):
        if len(self.__reservation) == 0:
            self.__get_reservations()

        if len(self.__reservation) == 0:
            print("you have no one reservation!")
            return

        self.__action_reservation.cancel_reservation(id, self.__session)

    def prepare(self):
        self.__check_identification()
        self.__get_reservations()
        self.__action_reservation = Reservation()

    def flush_identification(self):
        self.__session = None
        self.__check_identification()
        self.__action_reservation = Reservation()

    def get_identification(self):
        return self.__session

    def make_reservation(self, start: str, end: str, dev_id: str):
        self.__action_reservation.make_reservation(start, end, dev_id,self.get_identification())

    def find_seat(self,  start: str, end: str):
        ci = get_construction_info(self.get_identification())
        ci.prepare()
        data = ci.find_seat(start, end, self.__priority)
        return data

    def set_priority(self,priority:list[str]):
        self.__priority = priority