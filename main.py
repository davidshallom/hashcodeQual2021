from database import Database
from solver import Solver
from os import listdir
import numpy as np

if __name__ == '__main__':
    # file_names = listdir("./input_files")
    total_score = 0
    file_names = ["d.txt"]
    for file_name in file_names:
        in_file_path = "./input_files/" + file_name
        for p in range(0, 30, 5):
            database = Database(in_file_path)
            database.display_parms()
            if file_name in ["f.txt", "d.txt"]:
                solver = Solver(database, prec_to_remove=p)
            else:
                solver = Solver(database)

            if file_name in ["e.txt"]:
                solver.set_initial_schedule()
            else:
                solver.zero_sched()
                solver.create_prioritized_sched(normalization=2)

            score = solver.calc_score()
            print(f"File name - {file_name} - Score = {score}")
            total_score += score

        print(f"Total score = {total_score}")
