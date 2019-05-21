
"""Wrapper script for testing the performance of SpamBayes.

Run a canned mailbox through a SpamBayes ham/spam classifier.
"""

import os.path

import pyperf

from spambayes import hammie, mboxutils


__author__ = "skip.montanaro@gmail.com (Skip Montanaro)"
__contact__ = "collinwinter@google.com (Collin Winter)"


def bench_spambayes(ham_classifier, messages):
    for msg in messages:
        ham_classifier.score(msg)


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Run the SpamBayes benchmark."

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    mailbox = os.path.join(data_dir, "spambayes_mailbox")
    ham_data = os.path.join(data_dir, "spambayes_hammie.pkl")
    messages = list(mboxutils.getmbox(mailbox))
    ham_classifier = hammie.open(ham_data, "pickle", "r")

    runner.bench_func('spambayes', bench_spambayes, ham_classifier, messages)
