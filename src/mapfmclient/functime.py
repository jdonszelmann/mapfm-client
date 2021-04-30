from time import perf_counter


def time_fun(problem, funct):
    s = perf_counter()
    solution = funct(problem)
    e = perf_counter() - s
    return solution, e
