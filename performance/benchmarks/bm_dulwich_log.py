import os

import perf.text_runner
from six.moves import xrange

import dulwich.repo


def test_dulwich(loops, repo_path):
    repo = dulwich.repo.Repo(repo_path)
    head = repo.head()
    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        # iterate on all changes on the Git repository
        for entry in repo.get_walker(head):
            pass

    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='dulwich_log')
    runner.metadata['description'] = ("Dulwich benchmark: "
                                      "iterate on all Git commits")

    repo_path = os.path.join(os.path.dirname(__file__), 'data', 'asyncio.git')
    runner.bench_sample_func(test_dulwich, repo_path)
