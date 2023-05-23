from internal.info.reservation import ReservationInfo
from internal.util.util import *

class SeatInfo:
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.__data = data
        self.room_name = self.__data["roomName"]
        self.seat_no = self.__data["title"]
        self.__reservations: list[ReservationInfo] = []
        self.spare_time: list[tuple[str, str]] = []
        self.dev_id = data['devId']
        self.__length = 0
        self.__get_reservation()

    def show_seat_info(self):
        print(f"    reservations on {self.seat_no} of {self.room_name}:")
        for one in self.__reservations:
            one.show_reservation()

    def __get_reservation(self):
        for one in self.__data["ts"]:
            self.__length += 1
            self.__reservations.append(ReservationInfo(
                one["start"], one["end"], one["date"], one["owner"],
            ))

    def get_length(self):
        return self.__length

    def get_spare_time(self, start: str, end: str, gap: int, show: bool):
        arrangement: list[tuple[str, str]] = []

        for one in self.__reservations:
            arrangement.append((one.start.split()[1], one.end.split()[1]))
        arrangement.sort(key=lambda ele: ele[0])

        now = get_time()
        if compare_with_word(start, now, 0) == "":
            now = start
        arrangement.insert(0, ("", now))
        arrangement.append((end, ""))

        exist = False
        for i in range(1, len(arrangement)):
            if compare_with_word(arrangement[i - 1][1], arrangement[i][0], gap):
                if not exist and show:
                    print(f"{self.dev_id}:{self.seat_no}'s spare time:")
                if show:
                    print(f"\t{arrangement[i - 1][1]} - {arrangement[i][0]}")
                exist = True
                self.spare_time.append((arrangement[i - 1][1], arrangement[i][0]))