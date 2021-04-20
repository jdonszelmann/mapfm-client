import json
from typing import Union, List, Tuple


class Path:
    def __init__(self):
        self.route: List[Tuple[int, int]] = []

    @classmethod
    def from_list(cls, route: List[Tuple[int, int]]) -> "Path":
        res = cls()
        res.route = route
        return res

    def serialize(self) -> dict:
        return {
            "route": [
                {"x": i[0], "y": i[1]} for i in self.route
            ]
        }


class Solution:
    def __init__(self):
        self.paths = []

    @classmethod
    def from_paths(cls, paths: List[Union[Path, List[Tuple[int, int]]]]) -> "Solution":
        res = cls()
        res.paths = [i if isinstance(i, Path) else Path.from_list(i) for i in paths]
        return res

    def add_path(self, path: Path, for_agent_index: Union[int, None] = None):
        self.paths.append(path)

    def serialize(self) -> dict:
        return {
            "paths": [
                i.serialize() for i in self.paths
            ]
        }
