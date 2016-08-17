import perf
from six.moves import xrange

from pybench import Test


class IfThenElse(Test):

    version = 2.0
    operations = 30*3 # hard to say...
    inner_loops = 30

    def test(self, loops):
        a, b, c = 1,2,3
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

        return perf.perf_counter() - t0


class NestedForLoops(Test):

    version = 2.0
    operations = 1000*10*5
    inner_loops = 1000 * 10 * 5

    def test(self, loops):
        l1 = range(1000)
        l2 = range(10)
        l3 = range(5)
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            for i in l1:
                for j in l2:
                    for k in l3:
                        pass

        return perf.perf_counter() - t0


class ForLoops(Test):

    version = 2.0
    operations = 5 * 5
    # body repeated 25 items, each operation iterations 100 times
    inner_loops = 25 * 100

    def test(self, loops):

        l1 = range(100)
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

        return perf.perf_counter() - t0
