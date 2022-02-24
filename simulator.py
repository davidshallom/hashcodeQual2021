from collections import defaultdict
import numpy as np
import json
import copy

class Solver_Car():
    def __init__(self, indx, street_list):
        self.indx = indx
        self.s_names = street_list
        self.current_street_indx = 0
        self.current_street = street_list[self.current_street_indx]
        self.current_state = "Waiting"  # "Moving" / "Done"
        self.remaining_time = 0
        self.num_streets = len(street_list)

    def move_street(self, street_to_delay_dict):
        self.current_street_indx += 1
        self.current_street = self.s_names[self.current_street_indx]
        self.current_state = "Moving"
        self.remaining_time = street_to_delay_dict[self.current_street]

    def is_done(self):
        return self.current_state == "Done" or (
                    self.remaining_time == 0 and self.current_street_indx == self.num_streets - 1)


class Solver_Intersection():
    def __init__(self, indx, street_list):
        self.indx = indx
        self.s_names = street_list
        self.trafic_light_timing = []
        self.street_to_waiting_cars = defaultdict(list)
        self.street_to_sum_waiting = defaultdict(int)

    def set_traffic_light_timing(self, tl_timing):
        # tl_timing - list of tuples : (street name, green time)
        self.trafic_light_timing = tl_timing

    def get_current_street_with_green_light(self, t):
        tl_timing = [v[1] for v in self.trafic_light_timing]
        cycle_time = sum(tl_timing)
        if cycle_time == 0:
            return None
        offset = t % cycle_time
        ranges = np.cumsum(tl_timing)
        num_tl_streets = len(self.trafic_light_timing)
        for i in range(num_tl_streets):
            if offset < ranges[i]:
                return self.trafic_light_timing[i][0]
        raise Exception("Should not reach this")

    def get_current_freed_car(self, t):
        green_street = self.get_current_street_with_green_light(t)
        if green_street is None:
            return None
        waiting_cars = self.street_to_waiting_cars[green_street]
        if len(waiting_cars) == 0:
            return None
        return waiting_cars[0].indx

    def add_waiting_car(self, car, street_name):
        self.street_to_waiting_cars[street_name].append(car)

    def remove_car(self, car, street_name):
        self.street_to_waiting_cars[street_name].remove(car)


class Simulator():
    def __init__(self, car_list, intersections, street_to_delay, street_to_intersection, F, D, intr_to_tl_timing):
        self.car_list = car_list
        self.intersections = intersections
        #         self.car_to_length = car_to_length

        for intr_id, tl_timing in intr_to_tl_timing.items():
            self.intersections[intr_id].trafic_light_timing = tl_timing

        self.street_to_delay = street_to_delay
        self.street_to_intersection = street_to_intersection
        self.F = F
        self.D = D
        self.score = 0

    def step(self, t):
        #         print(f"{t}", end=" ")
        for car in self.car_list:
            if car.current_state == "Moving":
                car.remaining_time -= 1
                if car.is_done():
                    car.current_state = "Done"
                    #                     print(f"car {car.indx} is done")
                    self.score += self.F + self.D - t
                elif car.remaining_time == 0:
                    car.current_state = "Waiting"
                    intr_id = self.street_to_intersection[car.current_street]
                    intr = self.intersections[intr_id]
                    intr.add_waiting_car(car, car.current_street)

        for intr in self.intersections.values():
            for s_name, waiting_cars in intr.street_to_waiting_cars.items():
                #                 weight = 0
                #                 for c in waiting_cars:
                #                     weight += self.car_to_length[c.indx]
                intr.street_to_sum_waiting[s_name] += len(waiting_cars)
            #                 intr.street_to_sum_waiting[s_name] += weight
            freed_car_indx = intr.get_current_freed_car(t)
            if freed_car_indx is None:
                continue
            freed_car = self.car_list[freed_car_indx]
            #             print(f"car {freed_car.indx} freed from {freed_car.current_street}")
            intr.remove_car(freed_car, freed_car.current_street)
            freed_car.move_street(self.street_to_delay)

    #             print(f"car {freed_car.indx} continues to {freed_car.current_street}")

    def calc_score(self):
        self.score = 0
        for t in range(self.D):
            self.step(t)
        return self.score


class Solver_Parsser():
    def __init__(self, input_path):
        lines = [l.strip() for l in open(input_path, "r").readlines()]
        self.D, self.I, self.S, self.V, self.F = list(map(int, lines[0].split(" ")))
        street_to_intersection = {}
        street_to_delay = {}
        intr_to_streets = defaultdict(list)
        for line in lines[1:1 + self.S]:
            fields = line.split(" ")
            B, E = list(map(int, fields[:2]))
            s_name = fields[2]
            L = fields[3]
            street_to_delay[s_name] = int(L)
            street_to_intersection[s_name] = E
            intr_to_streets[E].append(s_name)

        intersections = {}
        for intr_id, s_names in intr_to_streets.items():
            intr = Solver_Intersection(intr_id, s_names)
            intersections[intr_id] = intr

        car_list = []
        for i, line in enumerate(lines[1 + self.S:]):
            fields = line.split(" ")
            P = int(fields[0])
            s_names = fields[1:]
            car = Solver_Car(i, s_names)
            car_list.append(car)
            start_street = s_names[0]
            intr = intersections[street_to_intersection[start_street]]
            intr.add_waiting_car(car, start_street)

        car_to_length = {}
        for car in car_list:
            l_sum = 0
            for s_name in car.s_names:
                l_sum += street_to_delay[s_name]
            car_to_length[car.indx] = l_sum

        self.car_list = car_list
        self.intersections = intersections
        self.street_to_intersection = street_to_intersection
        self.street_to_delay = street_to_delay
        self.car_to_length = car_to_length
