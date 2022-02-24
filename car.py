
class Car():
    def __init__(self, id, street_names):
        self.id = id
        self.street_names = street_names
        self.route_time = -1

    def calculate_route_time(self, street_dict):
        self.route_time = 0
        for s_name in self.street_names:
            self.route_time += street_dict[s_name].length