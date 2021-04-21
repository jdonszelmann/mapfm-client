import json
from time import time
from typing import List

from .solution import Solution
from .status import Status


class MarkedLocation:
    def __init__(self, color: int, x: int, y: int):
        self.color: int = color
        self.x: int = x
        self.y: int = y

    @classmethod
    def from_dict(cls, dct) -> "MarkedLocation":
        return cls(dct["color"], dct["x"], dct["y"])


class Problem:
    def __init__(self,
                 grid: List[List[int]],
                 width: int,
                 height: int,
                 starts: List[MarkedLocation],
                 goals: List[MarkedLocation],
                 benchmark,
                 identifier: int,
                 batch_pos: int
                 ):
        """
        MAPF problem with some extra data for the benchmark

        :param grid: a 2d array of integers. 1 means a wall, 0 means open
        :param width: width of the grid
        :param height: height of the grid
        :param starts: a list of `MarkedLocation`s representing starting positions for agents.
                       Each one has a color associated.
        :param goals: a list of `MarkedLocation`s representing goal positions for agents.
                       Each one has a color associated.
        :param benchmark: benchmarker this problem is associated with
        :param identifier: benchmark uuid
        :param batch_pos: position in the batch (if applicable)

        Note: There are always just as many goal locations of any color as there are agent start locations
        of that same color.
        """

        # USEFUL FOR PROBLEM SOLVING
        self.grid: List[List[int]] = grid
        self.width: int = width
        self.height: int = height
        self.starts: List[MarkedLocation] = starts
        self.goals: List[MarkedLocation] = goals

        # NOT NEEDED FOR THE PROBLEM SOLVING
        # FOR THE BENCHMARK ONLY
        self.benchmark = benchmark
        self.identifier = identifier
        self.batch_pos = batch_pos
        self.start_time = time()
        self.time = 0

        self.solution: Solution = Solution()
        self.status = {"state": Status.Uninitialized, "data": None}

    def __str__(self):
        out = f"<Problem\n" \
            f"\tWidth: {self.width}\n" \
            f"\tHeight: {self.height}\n" \
            f"\tStarts: {self.starts}\n" \
            f"\tGoals: {self.goals}\n" \
            f"\tGrid:\n"
        out += "\n".join("\t" + "".join(" " if it == 0 else "X" for it in row) for row in self.grid)
        out += "\n>"
        return out

    def set_solution(self, solution: Solution, runtime=None):
        """
        Add a solution to the problem

        :param solution: the solutions to this problem
        :param runtime: the time it took to calculate this solution
        """
        assert self.benchmark.status["state"] == Status.Running, \
            f"Benchmark seems to be inactive. state: {self.benchmark.status(['state'])})"
        assert self.benchmark.status["data"]["problem_states"][self.batch_pos] == 0, \
            "Problem seems to be already solved"

        self.solution = solution
        if runtime:
            self.time = runtime
        else:
            self.time = time() - self.start_time
        self.benchmark.status["data"]["problem_states"][self.batch_pos] = 1

        # when all benchmarks are done, submit the result
        if all(self.benchmark.status["data"]["problem_states"]):
            self.status = {"state": Status.Submitting, "data": None}
            self.benchmark.submit()

    @staticmethod
    def from_json(data, benchmark, batch_pos):
        """
        Generate problem from json
        :param data: json data
        :param benchmark: benchmark for submission callback
        :param batch_pos: position in benchmark
        :return:
        """
        return Problem(data["grid"], data["width"], data["height"], [MarkedLocation.from_dict(i) for i in data["starts"]],
                       [MarkedLocation.from_dict(i) for i in data["goals"]], benchmark, data["id"], batch_pos)
