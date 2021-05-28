from typing import TypeVar, List, Callable, Optional, Tuple

from .problem import Problem
from .parser import MapParser
from .test_bench import TestBench


class LocalSolver:
    """

    :param map_root: Root of folders with problem map folders
    :param cores: The number of cpu cores to run benchmarks on.
                  Each individual benchmark is still ran on the same core.
                  Set to -1 to use all cores available.
    :param timeout: The timeout for each benchmark *in milliseconds*. Set to None to disable.
    """

    a = TypeVar("a")

    def __init__(self, map_root: str, cores: int = -1, timeout: Optional[int] = None):
        self.parser = MapParser(map_root)
        self.test_bench = TestBench(cores, timeout)
        self.timeout = timeout
        self.map_root = map_root
        self.cores = cores

    def solve(
        self, solver: Callable[[Problem], a], folder_path: str
    ) -> List[Tuple[Problem, Optional[a], float]]:
        problems = self.parser.parse_batch(folder_path)
        return self.test_bench.run(solver, problems)
