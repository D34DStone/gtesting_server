from random import randint
from json import dump

from source import solve

NTEST = 50

if __name__ == "__main__":
    tests = []
    for _ in range(NTEST):
        n = randint(1, 25)
        m = randint(1, 25)
        data = [n, m] + [randint(1, 1e4) for _ in range(n * m * 2)]
        solution = solve(data)
        tests.append({
            "input": [str(n) for n in data],
            "output": [str(n) for n in solution]})
    testset = { "tests": tests }
    with open("testset.json", "w") as f:
        dump(testset, f)
