import json
from time import perf_counter
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

    def serialize(self):
        return {
            "color": self.color,
            "x": self.x,
            "y": self.y,
        }

    def __repr__(self):
        return f"MarkedLocation({self.x}, {self.y}, color={self.color})"

class Problem:
    def __init__(self,
                 grid: List[List[int]],
                 width: int,
                 height: int,
                 starts: List[MarkedLocation],
                 goals: List[MarkedLocation],
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

        Note: There are always just as many goal locations of any color as there are agent start locations
        of that same color.
        """

        # USEFUL FOR PROBLEM SOLVING
        self.grid: List[List[int]] = grid
        self.width: int = width
        self.height: int = height
        self.starts: List[MarkedLocation] = starts
        self.goals: List[MarkedLocation] = goals

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

    @staticmethod
    def from_json(data):
        """
        Generate problem from json
        :param data: json data
        :return:
        """
        return Problem(data["grid"], data["width"], data["height"], [MarkedLocation.from_dict(i) for i in data["starts"]],
                       [MarkedLocation.from_dict(i) for i in data["goals"]])
