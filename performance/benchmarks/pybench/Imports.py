import perf
from six.moves import xrange

from pybench import Test

# First imports:
import os                  # noqa
import package.submodule   # noqa


class SecondImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa

            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa

            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa

            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa

            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa
            import os   # noqa

        return perf.perf_counter() - t0


class SecondPackageImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa

            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa

            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa

            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa

            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa
            import package   # noqa

        return perf.perf_counter() - t0


class SecondSubmoduleImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa

            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa

            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa

            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa

            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa
            import package.submodule   # noqa

        return perf.perf_counter() - t0
