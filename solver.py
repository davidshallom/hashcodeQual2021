import numpy as np
from intersection import Intersection
from simulator import *
from matplotlib import pyplot as plt
import random
from multiprocessing import Pool, cpu_count
import numpy as np
from collections import OrderedDict
import math
from os import path

class Solver():
    def __init__(self, database, prec_to_remove):
        self.intersections = [Intersection(i) for i in range(database.num_intr)]
        self.database = database
        self.update_cars(prec_to_remove)
        self.update_intersections()
        self.avg_wait = None
        self.score_list = None

    def zero_sched(self):
        for intr in self.intersections:
            intr.schedule = OrderedDict()

    def update_cars(self, prec_num_to_remove=0):
        for car in self.database.cars:
            car.calculate_route_time(self.database.street_dict)
        time_to_car = [(car.route_time, car) for car in self.database.cars]
        time_to_car.sort(key=lambda x: x[0], reverse=True)
        num_to_remove = int(len(self.database.cars) * prec_num_to_remove / 100)
        remain_cars = [v[1] for v in time_to_car[num_to_remove:]]
        self.database.cars = remain_cars

    def update_intersections(self):
        for street_name, street in self.database.street_dict.items():
            self.intersections[street.e_intr].add_incoming_street(street_name)

        relevant_cars = [c for c in self.database.cars if c.route_time < self.database.simulation_time]
        print(f"{len(relevant_cars)} / {len(self.database.cars)} relevant cars")
        for car in relevant_cars:
            for s_name in car.street_names[:-1]: #igonring the last street
                street = self.database.street_dict[s_name]
                self.intersections[street.e_intr].increment_car_count(street.name)
                self.intersections[street.e_intr].increment_ce(street.name, 1/car.route_time)

    def set_initial_schedule(self):
        for intr in self.intersections:
            count_to_str_name = sorted([(v["count_cars"], k) for k, v in intr.streets.items()], reverse=True)
            count_zeros = len([v for v in count_to_str_name if v[0] == 0])
            remain_time = self.database.simulation_time
            for cnt, s_name in count_to_str_name:
                if remain_time <= 0 or cnt == 0:
                    break
                # intr.schedule[s_name] = cnt
                intr.schedule[s_name] = 1
                remain_time -= cnt

    def create_prioritized_sched(self, normalization=2):
        for intr in self.intersections:
            total_ce = sum([v["count_ce"] for v in intr.streets.values()])
            if total_ce == 0:
                continue

            num_seconds_to_distribute = len([v for v in intr.streets.values() if v["count_cars"] != 0]) * normalization
            for s_name, values in intr.streets.items():
                s_time = int(math.ceil((values["count_ce"] / total_ce) * num_seconds_to_distribute))
                intr.schedule[s_name] = s_time

    def get_average_waiting_time(self, car):
        avg_wait = 0
        wait_dict = {}
        for s_name in car.street_names[:-1]:
            street = self.database.street_dict[s_name]
            avg_wait += street.length
            e_intr = street.e_intr
            sched = self.intersections[e_intr].schedule
            if street.name not in sched:
                avg_wait += np.inf
                break
            max_wait = sum([v for k, v in sched.items() if k != s_name])
            p_free = sched[s_name] / sum(sched.values())
            delta = (1-p_free) * max_wait / 2
            wait_dict[e_intr] = (delta, street)
            avg_wait += delta

        return avg_wait, wait_dict

    def print_solution_to_file(self, output_path):
        intrs_with_sched = [intr for intr in self.intersections if intr.schedule != {}]
        A = len(intrs_with_sched)
        assert A != 0, "No scheduled intersections"
        with open(output_path, "w") as fh:
            fh.write(f"{A}\n")
            for intr in intrs_with_sched:
                fh.write(f"{intr.id}\n")
                sched_len = len(intr.schedule)
                fh.write(f"{len(intr.schedule)}\n")
                for s_name, sched_time in intr.schedule.items():
                    fh.write(f"{s_name} {sched_time}\n")

    def plot_average_wait(self):
        vals = sorted([self.get_average_waiting_time(car)[0] for car in self.database.cars])
        plt.figure()
        plt.plot(vals)
        plt.show()

    def calc_average_score(self):
        self.avg_wait = [self.get_average_waiting_time(car)[0] for car in self.database.cars]
        self.score_list = []
        for w in self.avg_wait:
            if w < self.database.simulation_time:
                self.score_list.append(self.database.bonus + self.database.simulation_time - w)
            else:
                self.score_list.append(0)
        # self.score_list = [self.database.bonus + self.database.simulation_time - w for w in self.avg_wait
        #                    if w < self.database.simulation_time else 0]
        return sum(self.score_list)

    def step_and_report(self, R):
        self.calc_average_score()
        w, cars = list(zip(*[((1 / (wt - self.database.simulation_time)), car) for wt, sc, car in
                             zip(self.avg_wait, self.score_list, self.database.cars) if sc == 0]))
        sum_w = sum(w)
        p = [v / sum_w for v in w]
        selected_car_indx = np.random.choice(range(len(cars)), p=p)
        selected_car = cars[selected_car_indx]
        required_fix = self.get_average_waiting_time(selected_car)[0] - self.database.simulation_time
        # print(f"required_fix={required_fix}")

        w_time, wait_dict = self.get_average_waiting_time(selected_car)
        intrs, w_p_street = list(zip(*wait_dict.items()))
        w, streets = list(zip(*w_p_street))
        sum_w = sum(w)
        p = [v / sum_w for v in w]
        intr_id = np.random.choice(range(len(intrs)), p=p)
        intr, street = self.intersections[intrs[intr_id]], streets[intr_id]
        items = list(intr.schedule.items())
        random.shuffle(items)
        intr.schedule = OrderedDict(items)
        rand_keys = [k for k in intr.schedule.keys() if k != street.name]
        dec_key = random.choice(rand_keys)
        # intr.schedule[dec_key] -= random.randrange(0, min(int(required_fix), intr.schedule[dec_key]))
        # intr.schedule[dec_key] -= min(intr.schedule[dec_key]-1, math.ceil(required_fix))
        intr.schedule[street.name] += 1
        return self.calc_average_score()

    def run_parallel_simulated_annealing(self, strategy, start_score,
                                         start_temprature, end_temprature, decr):

        """
        strategy - p(accept better solution), p(accept worse solution) -
                    "A" - (1, 0), "B" - (p, 0), "C" - (1, p), "D" (p, p)
        start_temprature (end_temprature) - initial temprature (and end temprature)
        decr - the temprature decrement between consecutive iterations
        num_processes - the number of processes that the function generates for when looking for a new solution
        output_dir - the output directory - the function writes intermediate best results to this directory
        output_fname - the base name for the generated output files
        """

        curr_intersections, curr_score = copy.deepcopy(self.intersections), start_score  # consider using copy.deepcopy()
        best_intersections, best_score = copy.deepcopy(curr_intersections), curr_score

        # if num_processes > cpu_count():
        #     print(f"Warning - you are creating {num_processes} processes but you only have {cpu_count()} cores")

        # print(f'starting computations on {cpu_count()} actual cores, using {num_processes} processes')

        T = start_temprature
        while T > end_temprature:
            res = self.step_and_report(T)
            diff = res - curr_score
            if diff > 0:
                if strategy == "A" or strategy == "C":
                    acceptance_p = 1
                else:
                    acceptance_p = 1 - math.exp(- diff / T)
                print(f"T:{T} - New improved score {res}, diff = {diff}, acceptance probability = {acceptance_p}")
                if res > best_score:
                    best_intersections, best_score = copy.deepcopy(self.intersections), res
                if random.uniform(0, 1) >= acceptance_p:
                    self.intersections, curr_score = curr_intersections, curr_score
                    print("not accepted")
                else:
                    curr_intersections, curr_score = copy.deepcopy(self.intersections), res
                    print("accepted")
            elif (strategy == "C" or strategy == "D") and diff < 0:
                acceptance_p = math.exp(diff / T)
                print(
                    f"T:{T} - Did not improve the score. New score = {res}, diff = {diff}, acceptance probability = {acceptance_p}")
                if random.uniform(0, 1) >= acceptance_p:
                    self.intersections, curr_score = curr_intersections, curr_score
                    print("not accepted")
                else:
                    curr_intersections, curr_score = copy.deepcopy(self.intersections), res
                    print("accepted")
            T = T - decr
        self.intersections = best_intersections
        print(f"After running SIMA, score is {best_score}")

    def calc_score(self):
        parser = Solver_Parsser(self.database.input_path)
        intr_to_tl_timing = {}
        for indx, intr in enumerate(self.intersections):
            intr_to_tl_timing[indx] = list(intr.schedule.items())
        simulator = Simulator(parser.car_list,
                              parser.intersections,
                              parser.street_to_delay,
                              parser.street_to_intersection,
                              parser.F,
                              parser.D,
                              intr_to_tl_timing)
        return simulator.calc_score()

    def shuffle_schedule(self):
        for intr in self.intersections:
            items = list(intr.schedule.items())
            random.shuffle(items)
            intr.schedule = OrderedDict(items)
