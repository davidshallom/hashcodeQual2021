from car import Car
from street import Street

class Database():
    def __init__(self, input_path):
        self.input_path = input_path
        with open(input_path) as fh:
            lines = [l.strip() for l in fh.readlines()]
        self.simulation_time, self.num_intr, self.num_streets, self.num_cars, self.bonus = map(int, lines[0].split(" "))

        street_dict = {}
        for l in lines[1 : 1 + self.num_streets]:
            fields = l.split(" ")
            street = Street(b_intr=int(fields[0]), e_intr=int(fields[1]), name=fields[2], length=int(fields[3]))
            street_dict[street.name] = street
        assert len(street_dict.keys()) == self.num_streets, "Number of streets do not match"

        cars = []
        for indx, l in enumerate(lines[1 + self.num_streets:]):
            fields = l.split(" ")
            num_streets = int(fields[0])
            street_names = fields[1:]
            assert len(street_names) == num_streets, "Number of streets do not much the P parameter"
            car = Car(id=indx, street_names=street_names)
            cars.append(car)
        assert len(cars) == self.num_cars, "Number of cars do not match"

        self.street_dict = street_dict
        self.cars = cars

    def display_parms(self):
        print(f"{self.input_path} - input Parameters:")
        print("self.simulation_time = {}, self.num_intr = {}, self.num_streets = {}, self.num_cars = {}, " \
                "self.bonus = {}".format(self.simulation_time,
                                         self.num_intr, self.num_streets, self.num_cars, self.bonus))