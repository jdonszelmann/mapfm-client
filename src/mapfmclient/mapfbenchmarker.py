from pathos.multiprocessing import ProcessPool as Pool
from typing import Union, Callable, List, Iterable, Optional, Tuple
from urllib.parse import urljoin

from tqdm import tqdm

from .functime import time_fun

from .problem import Problem
from .solution import Solution
from .status import Status

import requests
from func_timeout import func_timeout, FunctionTimedOut


class InvalidResponseException(Exception):
    pass


class ProgressiveDescriptor:
    def __init__(self, min_agents: int, max_agents: int, num_teams: int, max_team_diff: int = 0):
        assert min_agents <= max_agents

        self.min_agents = min_agents
        self.max_agents = max_agents
        self.num_teams = num_teams
        self.max_team_diff = max_team_diff


    def serialize(self):
        return {
            "min_agents": self.min_agents,
            "max_agents": self.max_agents,
            "num_teams": self.num_teams,
            "max_diff": self.max_team_diff
        }


class BenchmarkDescriptor:
    def __init__(self, identifier: int, progressive_descriptor: Optional[ProgressiveDescriptor] = None):
        """
        :param identifier: identifies the benchmark, or  the progressive benchmark in case a progressive descriptor is
                           given.
        :param progressive_descriptor: When not None, runs a progressive benchmark (which needs some configuration).
        """

        self.identifier = identifier
        self.progressive_descriptor = progressive_descriptor

    @property
    def progressive(self) -> bool:
        return self.progressive_descriptor is not None


class MapfBenchmarker:
    def __init__(self,
                 token: str,
                 benchmark: Union[int, Iterable[int], BenchmarkDescriptor, Iterable[BenchmarkDescriptor]],
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
        :param benchmark: id (or ids) of the problem to solve. May also take problem descriptors
                          (internal representation, and useful for progressive benchmarks)
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
        self.benchmarks = []
        if isinstance(benchmark, int):
            self.benchmarks = [BenchmarkDescriptor(benchmark)]

        elif isinstance(benchmark, BenchmarkDescriptor):
            self.benchmarks = [benchmark]

        elif isinstance(benchmark, list):
            for i in benchmark:
                if isinstance(i, int):
                    self.benchmarks.append(BenchmarkDescriptor(i))
                elif isinstance(i, BenchmarkDescriptor):
                    self.benchmarks.append(i)
                else:
                    raise TypeError(
                        f"invalid type for benchmark: {i} (must be int, BenchmarkDescriptor, or list of one of these)"
                    )
        else:
            raise TypeError(
                f"invalid type for benchmark: {benchmark} (must be int, BenchmarkDescriptor, or list of one of these)"
            )

        self.problems = None
        self.timeout = None
        self.debug = debug
        self.cores = cores
        self.user_timeout = timeout

        self.baseURL = baseURL.rstrip("/")

    def _get_benchmark_data(self, descriptor: BenchmarkDescriptor, attempt: bool):
        return {
            "algorithm": self.algorithm,
            "version": self.version,
            "debug": self.debug,
            "progressive": descriptor.progressive,
            "progressive_description":
                descriptor.progressive_descriptor.serialize()
                if descriptor.progressive
                else None,
            "create_attempt": attempt,
        }

    def _get_benchmark(self, descriptor: BenchmarkDescriptor) -> List[Problem]:
        headers = {
            'X-API-Token': self.token
        }

        data = self._get_benchmark_data(descriptor, attempt=False)

        r = requests.post(f"{self.baseURL}/api/benchmark/attempt/{descriptor.identifier}", headers=headers, json=data)

        if r.status_code != 200:
            raise InvalidResponseException(f"Received invalid response from server ({r.status_code}) ({r.json()})")

        j = r.json()
        problems = [
            Problem.from_json(part)
            for part in j["benchmarks"]
        ]

        return problems

    def _start_attempt(self, descriptor: BenchmarkDescriptor) -> Tuple[List[Problem], int]:
        headers = {
            'X-API-Token': self.token
        }

        data = self._get_benchmark_data(descriptor, attempt=True)

        r = requests.post(f"{self.baseURL}/api/benchmark/attempt/{descriptor.identifier}", headers=headers, json=data)

        if r.status_code != 200:
            raise InvalidResponseException(f"Received invalid response from server ({r.status_code}) ({r.content})")

        j = r.json()
        problems = [
            Problem.from_json(part)
            for part in j["benchmarks"]
        ]

        return problems, j["attempt_id"]

    def run(self, *, solver: Optional[Callable[[Problem], Union[List, Solution]]] = None, make_attempt: bool = True):
        """
        Use your solver to solve all problems
        :param solver: alternative solver (or None)
        :param make_attempt: False if you do not intend to submit this
        """

        if solver is None:
            solver = self.solver
        assert solver is not None, \
            "No solver given.\n Consult the README for information about running timed benchmarks."

        for descriptor in self.benchmarks:
            try:
                if make_attempt:
                    problem_list, attempt_id = self._start_attempt(descriptor)
                else:
                    problem_list = self._get_benchmark(descriptor)
            except InvalidResponseException as e:
                print(f"invalid response on for: {descriptor} ({e})")
                continue


            if self.timeout:
                def solve_func(current_problem: Problem) -> Optional[Solution]:
                    try:
                        sol = func_timeout(self.timeout / 1000, self.solver, args=(current_problem,))

                    except FunctionTimedOut:
                        sol = None
                    except Exception as e:
                        print(f"An error occurred while running: {e}")
                        return None
                    return sol
            else:
                solve_func = self.solver

            def time_func(current_problem):
                return (current_problem, *time_fun(current_problem, solve_func))

            if self.cores == 1:
                solutions = list(tqdm(
                    map(time_func, problem_list),
                    total=len(problem_list)
                ))
            elif self.cores == -1:
                with Pool() as p:
                    solutions = list(tqdm(
                        p.imap(time_func, problem_list),
                        total=len(problem_list)
                    ))
            else:
                with Pool(self.cores) as p:
                    solutions = list(tqdm(
                        p.imap(time_func, problem_list),
                        total=len(problem_list)
                    ))

            if make_attempt:
                self._submit_solution(descriptor, solutions, attempt_id)

    def _submit_solution(self, descriptor: BenchmarkDescriptor, solutions: List[Tuple[Problem, Solution, float]], attempt_id: int):
        headers = {
           'X-API-Token': self.token
        }

        data = {
            "solutions": [
               {
                   "time": round(time * 1000 * 1000 * 1000),
                   "solution": solution.serialize(),
                   "progressive_params": {
                       "num_agents": len(problem.starts),
                       "num_teams": descriptor.progressive_descriptor.num_teams,
                       "max_diff": descriptor.progressive_descriptor.max_team_diff,
                   } if descriptor.progressive else None
               } for (problem, solution, time) in solutions
            ],
            "benchmark": descriptor.identifier,
            "progressive": descriptor.progressive,
        }

        r = requests.post(f"{self.baseURL}/api/solutions/submit/{attempt_id}", headers=headers, json=data)

        if r.status_code != 200:
            raise InvalidResponseException(f"Received invalid response from server ({r.status_code}) ({r.content})")


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
