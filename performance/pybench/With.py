from __future__ import with_statement

import perf
from six.moves import xrange

from pybench import Test


class WithFinally(Test):

    version = 2.0
    operations = 20
    inner_loops = 20

    class ContextManager(object):
        def __enter__(self):
            pass
        def __exit__(self, exc, val, tb):
            pass

    def test(self, loops):
        cm = self.ContextManager()
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass

        return perf.perf_counter() - t0


class TryFinally(Test):

    version = 2.0
    operations = 20
    inner_loops = 20

    class ContextManager(object):
        def __enter__(self):
            pass
        def __exit__(self):
            # "Context manager" objects used just for their cleanup
            # actions in finally blocks usually don't have parameters.
            pass

    def test(self, loops):
        cm = self.ContextManager()
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

        return perf.perf_counter() - t0


class WithRaiseExcept(Test):

    version = 2.0
    operations = 2 + 3 + 3
    inner_loops = 8

    class BlockExceptions(object):
        def __enter__(self):
            pass
        def __exit__(self, exc, val, tb):
            return True

    def test(self, loops):

        error = ValueError
        be = self.BlockExceptions()
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")

        return perf.perf_counter() - t0
