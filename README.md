# MAPFM Client

This is a client library for the https://mapf.nl/ MMAPF problems
## The MAPFM problem
MAPFM is an abbreviation of  "Matching in multi-agent pathfinding".
With MAPFM problems, you are given:
-	A grid/maze
-	A list of agent starting positions (each agent has a color)
-	A list of agent goal positions (each goal has a color)

The solution for that problem is a list of paths, one for each agent st.
-	Each path starts on the starting position of an agent
-	Each path ends on a goal position of the same color as the agent
-	No path crosses a wall in the grid
-	No 2 agents are ever on the same position at the same time
-	No 2 agents  ever cross the same edge (in opposite directions) at the same time
This solution is optimal if there is no other solution st. the sum of the lengths of the paths of all the agents is smaller than this solution.
## Using the client library
Install the library with:
```bash
pip install mapfmclient
```
Then go to https://mapf.nl/benchmarks/. Here you can find a list of benchmarks. If you click on a benchmark you can see prefiously posted solutions. By clicking on a solution, You can see what the problem looks like. Find a problem that you like, and find its index on the https://mapfw.nl/benchmarks/ page (Sorry, you will have to count yourself, starting from 1. This will change later).

Now go to your account page at https://mapfw.nl/auth/account. To find your API Token

This is all the info you need to start coding. The basic outline of your code should look like this:
```python
from mapfmclient import MapfwBenchmarker
if __name__ == '__main__':
    benchmarker = MapfwBenchmarker("<YOUR API TOKEN>", <BENCHMARK ID(s)>, "<YOUR ALGORITHMS NAME>",
                                   "<YOUR ALGORITHMS VERSION>", <DEBUG_MODE>, solver=<SOLVER>,cores=<CORES>)
    benchmarker.run()
```
The only things that you need to do are to fill in
- Your own API Token
- The number of the benchmark that you want to solve
- The name of your algorithm
- Its version qnd the debug mode. (This should be set to True while you are developing your algorithm. This means that your attempts will not be shown on the global leader boards. You can however still see your own solution at https://mapf.nl/latest-debug.)
- Your solver function
- The amount of cores that you want to use for this benchmark (Default=1. For all cores, use -1)

Note that the benchmark id does not need to be complete. Any uniquely identifying prefix of the id will work.
On https://mapf.nl, 5 characters are usually used.

You should implement the "solver" function yourself.
This function should take in a problem and return the solution.
A basic outline of this function can be as follows:
```python
from mapfmclient import Problem, Solution, MarkedLocation


class Maze:
    def __init__(self, grid, width, height):
        self.grid = grid
        self.width = width
        self.height = height


def solve(problem):
    maze = Maze(problem.grid, problem.width, problem.height)

    paths = []
    for agent in agents:
        paths.append(find_path(agent, maze))

    """
    Now paths looks like:
    
    paths = list[Path]
    Path = List[(x, y)]
    """

    return Solution.from_paths(paths)
```

It is also possible to run multiple benchmarks at the same time.
Instead of giving an integer as the benchmark index, you can also give an iterable to the ```MapfwBenchmarker``` constructor.
Valid uses are:

Run benchmark 3, with solver ```solve```, with algorithm TestAlgorithm and version TestVersion, in debug on 1 core:
```python
MapfBenchmarker("<YOUR API TOKEN>", 1, "TestAlgotithm",
                    "TestVersion", True, solver=solve,cores=1)
```

Run benchmark 1,2 and 3, with solver ```solve```, with algorithm TestAlgorithm and version TestVersion, in debug on 3 cores:
```python
MapfBenchmarker("<YOUR API TOKEN>", [1, 2, 3], "TestAlgotithm",
                    "TestVersion", True, solver=solve,cores=3)
```

If you want a list of all the indexes of the benchmarks, that is possible with the ```get_all_benchmarks``` function.
As an argument you can add the index, or a list of indexes of benchmarks that you dont want to run
```python
from mapfmclient import get_all_benchmarks
all_benchmarks = get_all_benchmarks()
without_benchmark_3 = get_all_benchmarks(without="3ab4d")
without_benchmark_2_and_4 = get_all_benchmarks(without=[1, 3, 4])
```

When your are ready, set the debug mode to False. The next time you run your code, your attempt will be publicly listed.

This should be all that you need to know to get started!
Please note that this is just some example code and feel free to change it however you like.

Good luck! And let us know if you have any questions.


Note: This client is largely an adaptation of a similar project for a different problem
called MAPFW (MAPF with waypoints). It can be found [here](https://github.com/noahiscool13/mapfw-client) 