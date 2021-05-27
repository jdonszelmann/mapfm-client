from pathos.multiprocessing import ProcessPool as Pool
from typing import List, TypeVar, Callable, Optional, Any

from tqdm import tqdm

from src.mapfmclient import Problem
from src.mapfmclient.timing import TimeoutSolver, TimingFunction


class TestBench:
    """
    Helper class for benchmarking solvers using problem sets. Execution times are recorded and a time-out can be set.

    :param cores: The number of cpu cores to run benchmarks on.
                  Each individual benchmark is still ran on the same core.
                  Set to -1 to use all cores available.
    :param timeout: The timeout for each benchmark *in milliseconds*. Set to None to disable.
    """

    def __init__(self, cores: int = -1, timeout: Optional[int] = None):
        self.cores = cores
        self.timeout = timeout

    def run(
        self, solver: Callable[[Problem], Any], problem_list: List[Problem]
    ) -> Any:
        if self.timeout:
            solve_func = TimeoutSolver(solver, self.timeout)
        else:
            solve_func = solver
        time_func = TimingFunction(solve_func)
        if self.cores == 1:
            solutions = list(
                tqdm(map(time_func, problem_list), total=len(problem_list))
            )
        elif self.cores == -1:
            with Pool() as p:
                solutions = list(
                    tqdm(p.imap(time_func, problem_list), total=len(problem_list))
                )
        else:
            with Pool(self.cores) as p:
                solutions = list(
                    tqdm(p.imap(time_func, problem_list), total=len(problem_list))
                )
        return solutions
