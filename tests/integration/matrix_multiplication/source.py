import sys 
from typing import Tuple, List


def solve(data):
    n, m, *data = data

    def arr_to_matrix(n: int, m: int, arr: List[int]) -> Tuple[List[List[int]], List[int]]:
        matrix = [[0 for _ in range(m)] for _ in range(n)]
        for i in range(n):
            for j in range(m):
                el, *arr = arr
                matrix[i][j] = el
        return matrix, arr

    m1, data = arr_to_matrix(n, m, data)
    m2, _ = arr_to_matrix(m, n, data)

    m3 = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(m):
                m3[i][j] += m1[i][k] * m2[k][j]

    return [item for sublist in m3 for item in sublist]


if __name__ == "__main__":
    data = [int(n) for n in sys.stdin.read().split()]
    print(" ".join(str(n) for n in solve(data)))
