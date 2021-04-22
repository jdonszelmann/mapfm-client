from pathos.multiprocessing import ProcessPool as Pool
from typing import Union, Callable, List, Iterable, Optional

from tqdm import tqdm

from .functime import time_fun

from .problem import Problem
from .solution import Solution
from .status import Status

import requests
from func_timeout import func_timeout, FunctionTimedOut


class MapfBenchmarker:
    def __init__(self,
                 token: str,
                 problem_id: Union[int, Iterable[int]],
                 algorithm: str,
                 version: str,
                 debug: bool = True,
                 solver: Optional[Callable[[Problem], Union[List, Solution]]] = None,
                 cores: int = 1,
                 timeout: Union[int, None] = 10,
                 baseURL: str = "https://mapf.nl/"
                 ):
        """
        Class to help handle API requests

        :param token: Your user token.
        :param problem_id: UUID (or the first part of the uuid) of the problem to solve.
        :param algorithm: The name of your algorithm.
        :param version: The version of your algorithm.
        :param debug: Set to False to get your solution in the global rankings.
        :param solver: Your MAPFW solving function.
        :param cores: The number of cpu cores to run benchmarks on.
                      Each individual benchmark is still ran on the same core.
                      Set to -1 to use all cores available.
        :param timeout: The timeout for each benchmark *in milliseconds*. Set to None to disable.
        :param baseURL: The url of the mapf server. Usually https://mapf.nl or https://dev.mapf.nl.
        """

        self.token = token
        self.solver = solver
        self.algorithm = algorithm
        self.version = version
        self.benchmarks = [problem_id] if isinstance(problem_id, int) else problem_id
        self.problems = None
        self.status = {"state": Status.Uninitialized, "data": None}
        self.attempt_id = None
        self.timeout = None
        self.debug = debug
        self.cores = cores
        self.user_timeout = timeout

        self.baseURL = baseURL.rstrip('/')

        self.problem_id: Union[int, None] = None

    def run(self, solver: Optional[Callable[[Problem], Union[Solution, List]]] = None):
        """
        Use your solver to solve all problems
        """
        if solver:
            self.solver = solver
        assert self.solver, "No solver given.\n Consult the README for information about running timed benchmarks."

        for problem_id in self.benchmarks:
            self.status = {"state": Status.Uninitialized, "data": None}
            self.problem_id = problem_id
            self.load()

            while self.status["state"] == Status.Running:
                if self.timeout:
                    def solve_func(problem: Problem) -> Union[Solution, None]:
                        try:
                            sol = func_timeout(self.timeout / 1000, self.solver, args=(problem,))

                        except FunctionTimedOut:
                            sol = None
                        except Exception as e:
                            print(f"An error occurred while running: {e}")
                            return Solution()
                        return sol
                else:
                    solve_func = self.solver

                def time_func(problem):
                    return time_fun(problem, solve_func)

                if self.cores == 1:
                    solutions = list(tqdm(map(time_func, self.problems), total=len(self.problems)))
                elif self.cores == -1:
                    with Pool() as p:
                        solutions = list(tqdm(p.imap(time_func, self.problems), total=len(self.problems)))
                else:
                    with Pool(self.cores) as p:
                        solutions = list(tqdm(p.imap(time_func, self.problems), total=len(self.problems)))

                for (p, (s, t)) in zip(self.problems, solutions):
                    p.set_solution(s if isinstance(s, Solution) else Solution.from_paths(s), runtime=t)

    def submit(self):
        """"
        Submit your solution
        You never have to call this function yourself,
        This will automatically be done when you solve all challenges.
        """

        headers = {
            'X-API-Token': self.token
        }

        data = [
            {
                "benchmark": problem.identifier,
                "time": round(problem.time * 1000 * 1000 * 1000),
                "solution": problem.solution.serialize()
            } for problem in self.problems
        ]

        r = requests.post(f"{self.baseURL}/api/solutions/{self.attempt_id}", headers=headers, json=data)

        assert r.status_code == 200, print(r.content)

        res = r.json()

        if res == "OK":
            self.status = {"state": Status.Submitted, "data": None}
        else:
            self.problems = [Problem.from_json(part, self, pos) for pos, part in enumerate(r.json()["problems"])]
            self.attempt_id = r.json()["attempt"]

            if "timeout" in r.json():
                timeout = r.json()["timeout"]
                if self.user_timeout:
                    self.timeout = min(self.user_timeout, timeout)
                else:
                    self.timeout = r.json()["timeout"]
            else:
                if self.user_timeout:
                    self.timeout = self.user_timeout
                else:
                    self.timeout = 0

            self.status = {"state": Status.Running, "data": {"problem_states": [0 for _ in self.problems]}}

    def load(self):
        """
        Load the benchmark from the server
        You never have to call this function yourself,
        This will automatically be done when you create an instance of this class.
        """

        assert self.status["state"] == Status.Uninitialized, "The benchmark seems to already been initialized\n"

        headers = {
            'X-API-Token': self.token
        }

        data = {
            "algorithm": self.algorithm,
            "version": self.version,
            "debug": self.debug
        }

        r = requests.post(f"{self.baseURL}/api/benchmark/{self.problem_id}", headers=headers,
                          json=data)

        assert r.status_code == 200, print(r.content)

        j = r.json()
        self.problems = [Problem.from_json(part, self, pos) for pos, part in enumerate(j["problems"])]
        self.attempt_id = j["attempt_id"]

        # TODO:
        # if "timeout" in r.json():
        #     timeout = r.json()["timeout"]
        #     if self.user_timeout:
        #         if self.user_timeout < timeout:
        #             warnings.warn(f"The benchmark recommended timeout is {timeout}ms,"
        #                           f" your timeout is {self.user_timeout}ms."
        #                           f" Consider increasing or removing your custom timeout.")
        #         if self.user_timeout > timeout:
        #             warnings.warn(f"The benchmark recommended timeout is {timeout}ms,"
        #                           f" your timeout is {self.user_timeout}ms."
        #                           f" Your timeout will be overwritten by the benchmark recommended timeout.")
        #         self.timeout = min(self.user_timeout, timeout)
        #     else:
        #         self.timeout = timeout
        #
        # else:
        #     if self.user_timeout:
        #         self.timeout = self.user_timeout
        #     else:
        #         self.timeout = 0

        self.status = {"state": Status.Running, "data": {"problem_states": [0 for _ in self.problems]}}


def get_all_benchmarks(without: Union[int, Iterable[int], None] = None, baseURL: str = "https://mapf.nl/"):
    """
    Get all benchmarks

    :param without: uuids to exclude
    :param baseURL:
    :return:
    """
    if not without:
        without = []
    without = [without] if isinstance(without, int) else without

    r = requests.get(f"{baseURL}/benchmarks/list.json")
    return [problem for problem in r.json() if problem not in without]
