from time import perf_counter
from typing import TypeVar, Callable, Optional, Tuple

from func_timeout import FunctionTimedOut, func_timeout

from .problem import Problem

a = TypeVar("a")
b = TypeVar("b")


def time_fun(problem: Problem, f: Callable[[a], b]) -> Tuple[b, float]:
    s = perf_counter()
    solution = f(problem)
    e = perf_counter() - s
    return solution, e


c = TypeVar("c")
d = TypeVar("d")


class TimeoutSolver:
    def __init__(self, solver: Callable[[c], d], timeout: int):
        self.solver = solver
        self.timeout = timeout

    def __call__(self, current_input: c) -> Optional[d]:
        try:
            solution = func_timeout(
                self.timeout / 1000, self.solver, args=(current_input,)
            )

        except FunctionTimedOut:
            solution = None
        except Exception as e:
            print(f"An error occurred while running: {e}")
            return None
        return solution


e = TypeVar("e")
f = TypeVar("f")


class TimingFunction:
    def __init__(self, solve_func: Callable[[e], f]):
        self.solve_func = solve_func

    def __call__(self, current_problem: e) -> Tuple[e, f, float]:
        result, time = time_fun(current_problem, self.solve_func)
        return current_problem, result, time
