from src.v2.tester import Report, Status
from src.v2.testing_strategy import TestResult


def print_report(report: Report):
    print("##### Test report #####")
    print(f"Status: {report.status.value}")
    if report.messages:
        print(f"Messages: {report.messages}")
    if report.test_results:
        print(f"Tests runned: {len(report.test_results)}")
        tests_repr = ["." if t.verdict == TestResult.Verdict.OK else "X" for t in report.test_results]
        print(f"Verdicts: {''.join(tests_repr)}")
    print()
