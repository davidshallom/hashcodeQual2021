from collections import OrderedDict

class Intersection():
    def __init__(self, id):
        self.id = id
        self.streets = {}
        self.schedule = OrderedDict()

    def add_incoming_street(self, street_name):
        self.streets[street_name] = {"count_cars": 0, "count_ce" : 0}

    def increment_car_count(self, street_name):
        self.streets[street_name]["count_cars"] += 1

    def increment_ce(self, street_name, val):
        self.streets[street_name]["count_ce"] += val


