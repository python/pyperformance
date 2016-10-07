import perf
from six.moves import intern, xrange

from pybench import Test


class ConcatStrings(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):

        # Make sure the strings are *not* interned
        s = ''.join(map(str, range(100)))
        t = ''.join(map(str, range(1, 101)))

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

        return perf.perf_counter() - t0


class CompareStrings(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):

        # Make sure the strings are *not* interned
        s = ''.join(map(str, range(10)))
        t = ''.join(map(str, range(10))) + "abc"

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

        return perf.perf_counter() - t0


class CompareInternedStrings(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):

        # Make sure the strings *are* interned
        s = intern(''.join(map(str, range(10))))
        t = s

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

        return perf.perf_counter() - t0


class CreateStringsWithConcat(Test):

    version = 2.0
    operations = 10 * 5

    def test(self, loops):

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            s = 'om'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

        return perf.perf_counter() - t0


class StringSlicing(Test):

    version = 2.0
    operations = 5 * 7
    inner_loops = 5

    def test(self, loops):

        s = ''.join(map(str, range(100)))

        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

        return perf.perf_counter() - t0


# String methods

if hasattr('', 'lower'):

    class StringMappings(Test):

        version = 2.0
        operations = 3 * (5 + 4 + 2 + 1)

        def test(self, loops):

            s = ''.join(map(chr, range(20)))
            t = ''.join(map(chr, range(50)))
            u = ''.join(map(chr, range(100)))
            v = ''.join(map(chr, range(256)))

            range_it = xrange(loops)
            t0 = perf.perf_counter()

            for _ in range_it:

                s.lower()
                s.lower()
                s.lower()
                s.lower()
                s.lower()

                s.upper()
                s.upper()
                s.upper()
                s.upper()
                s.upper()

                s.title()
                s.title()
                s.title()
                s.title()
                s.title()

                t.lower()
                t.lower()
                t.lower()
                t.lower()

                t.upper()
                t.upper()
                t.upper()
                t.upper()

                t.title()
                t.title()
                t.title()
                t.title()

                u.lower()
                u.lower()

                u.upper()
                u.upper()

                u.title()
                u.title()

                v.lower()

                v.upper()

                v.title()

            return perf.perf_counter() - t0

    class StringPredicates(Test):

        version = 2.0
        operations = 10 * 7
        inner_loops = 10

        def test(self, loops):

            data = ('abc', '123', '   ', '\xe4\xf6\xfc', '\xdf' * 10)
            len_data = len(data)

            range_it = xrange(loops)
            t0 = perf.perf_counter()

            for i in range_it:
                s = data[i % len_data]

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

            return perf.perf_counter() - t0
