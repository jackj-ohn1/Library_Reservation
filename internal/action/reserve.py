import datetime
import time

import orjson
import requests
from internal.util.util import *


class Reservation:
    ACTION_URL = 'http://kjyy.ccnu.edu.cn/ClientWeb/pro/ajax/reserve.aspx'

    def __init__(self):
        self.__reserve_params = {
            'type': 'dev',
            "start": "", "end": "",  # 2200
            'start_time': "", 'end_time': "",  # 2023-05-22 22:00
            'act': 'set_resv', '_': '', 'dev_id': '',
        }

        self.__cancel_params = {
            'id': '', '_': '', 'act': 'del_resv',
        }

    def cancel_reservation(self, rsv_id,session:requests.Session):
        self.__cancel_params['id'] = rsv_id
        self.__cancel_params['_'] = str(int(round(time.time() * 1000)))
        resp = session.get(url=Reservation.ACTION_URL, params=self.__cancel_params)
        print(orjson.loads(resp.text)['msg'])

    def make_reservation(self, start: str, end: str, dev_id: str, session: requests.Session):
        if session is None:
            raise Exception('please ensure your identification is not empty and useful!')
        # 预约应该是实时刷新的
        self.__reserve_params['dev_id'], self.__reserve_params['start_time'], self.__reserve_params['end_time'] = \
            dev_id, start.replace(':', ''), end.replace(':', '')

        self.__reserve_params['start'] = get_date() + ' ' + start
        self.__reserve_params['end'] = get_date() + ' ' + end

        resp = session.get(url=Reservation.ACTION_URL,params=self.__reserve_params)
        print(orjson.loads(resp.text)['msg'])
