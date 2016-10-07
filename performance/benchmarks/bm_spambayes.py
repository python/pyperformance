
"""Wrapper script for testing the performance of SpamBayes.

Run a canned mailbox through a SpamBayes ham/spam classifier.
"""

import os.path

from spambayes import hammie, mboxutils

import perf.text_runner
from six.moves import xrange


__author__ = "skip.montanaro@gmail.com (Skip Montanaro)"
__contact__ = "collinwinter@google.com (Collin Winter)"


def test_spambayes(loops, messages, ham_classifier):
    # Prime the pump. This still leaves some hot functions uncompiled; these
    # will be noticed as hot during the timed loops below.
    for msg in messages:
        ham_classifier.score(msg)

    range_it = xrange(loops)
    t0 = perf.perf_counter()

    for _ in range_it:
        for msg in messages:
            ham_classifier.score(msg)

    return perf.perf_counter() - t0


if __name__ == "__main__":
    runner = perf.text_runner.TextRunner(name='spambayes')
    runner.metadata['description'] = "Run the SpamBayes benchmark."

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    mailbox = os.path.join(data_dir, "spambayes_mailbox")
    ham_data = os.path.join(data_dir, "spambayes_hammie.pkl")
    msgs = list(mboxutils.getmbox(mailbox))
    ham_classifier = hammie.open(ham_data, "pickle", "r")

    runner.bench_sample_func(test_spambayes, msgs, ham_classifier)
