class ReservationInfo:
    def __init__(self, start="", end="", date="", owner="", data=None):
        if data is None:
            data = {}
        self.start, self.end, self.date, self.owner = start, end, date, owner
        self.data = data

    def show_reservation(self):
        print(f"        from {self.start} to {self.end}, {self.owner} is studying.")