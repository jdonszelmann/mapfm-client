from time import perf_counter
from typing import TypeVar, Callable, Optional, Tuple

from func_timeout import FunctionTimedOut, func_timeout

from src.mapfmclient import Problem

a = TypeVar("a")


def time_fun(problem: Problem, f: Callable[[Problem], a]) -> Tuple[a, float]:
    s = perf_counter()
    solution = f(problem)
    e = perf_counter() - s
    return solution, e


b = TypeVar("b")


class TimeoutSolver:
    def __init__(self, solver: Callable[[Problem], b], timeout: int):
        self.solver = solver
        self.timeout = timeout

    def __call__(self, current_problem: Problem) -> Optional[b]:
        try:
            solution = func_timeout(
                self.timeout / 1000, self.solver, args=(current_problem,)
            )

        except FunctionTimedOut:
            solution = None
        except Exception as e:
            print(f"An error occurred while running: {e}")
            return None
        return solution


c = TypeVar("c")


class TimingFunction:
    def __init__(self, solve_func: Callable[[Problem], c]):
        self.solve_func = solve_func

    def __call__(self, current_problem: Problem) -> Tuple[c, float]:
        return current_problem, *time_fun(current_problem, self.solve_func)
