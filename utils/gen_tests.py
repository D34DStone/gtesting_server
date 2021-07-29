import json 
import random 

if __name__ == "__main__":
    tests = list()
    for _ in range(100):
        a = random.randint(0, 1e18)
        b = random.randint(0, 1e18)
        tests.append({
            "input": [str(a), str(b)],
            "output": [str(a + b)]
        })
    json.dump(tests, open("sum_testset.json", "w"), indent=4)
