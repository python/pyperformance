import perf
import six
from six import unichr
from six.moves import xrange

from pybench import Test

if six.PY2:
    # On Python 2, unicode support is optional
    try:
        unicode
    except NameError:
        raise ImportError
else:
    unicode = str


class ConcatUnicode(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):
        # Make sure the strings are *not* interned
        s = unicode(u''.join(map(str, range(100))))
        t = unicode(u''.join(map(str, range(1, 101))))
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


class CompareUnicode(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):

        # Make sure the strings are *not* interned
        s = unicode(u''.join(map(str, range(10))))
        t = unicode(u''.join(map(str, range(10))) + "abc")
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


class CreateUnicodeWithConcat(Test):

    version = 2.0
    operations = 10 * 5
    inner_loops = 10 * 5

    def test(self, loops):
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for _ in range_it:
            s = u'om'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

            s = s + u'xax'
            s = s + u'xbx'
            s = s + u'xcx'
            s = s + u'xdx'
            s = s + u'xex'

        return perf.perf_counter() - t0


class UnicodeSlicing(Test):

    version = 2.0
    operations = 5 * 7
    inner_loops = 5 * 7

    def test(self, loops):
        s = unicode(u''.join(map(str, range(100))))
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

class UnicodeMappings(Test):

    version = 2.0
    operations = 3 * (5 + 4 + 2 + 1)

    def test(self, loops):

        s = u''.join(map(unichr, range(20)))
        t = u''.join(map(unichr, range(100)))
        u = u''.join(map(unichr, range(500)))
        v = u''.join(map(unichr, range(1000)))
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


class UnicodePredicates(Test):

    version = 2.0
    operations = 5 * 9
    inner_loops = 5 * 9

    def test(self, loops):

        data = (u'abc', u'123', u'   ', u'\u1234\u2345\u3456', u'\uFFFF' * 10)
        len_data = len(data)
        range_it = xrange(loops)
        t0 = perf.perf_counter()

        for i in range_it:
            s = data[i % len_data]

            s.isalnum()
            s.isalpha()
            s.isdecimal()
            s.isdigit()
            s.islower()
            s.isnumeric()
            s.isspace()
            s.istitle()
            s.isupper()

            s.isalnum()
            s.isalpha()
            s.isdecimal()
            s.isdigit()
            s.islower()
            s.isnumeric()
            s.isspace()
            s.istitle()
            s.isupper()

            s.isalnum()
            s.isalpha()
            s.isdecimal()
            s.isdigit()
            s.islower()
            s.isnumeric()
            s.isspace()
            s.istitle()
            s.isupper()

            s.isalnum()
            s.isalpha()
            s.isdecimal()
            s.isdigit()
            s.islower()
            s.isnumeric()
            s.isspace()
            s.istitle()
            s.isupper()

            s.isalnum()
            s.isalpha()
            s.isdecimal()
            s.isdigit()
            s.islower()
            s.isnumeric()
            s.isspace()
            s.istitle()
            s.isupper()

        return perf.perf_counter() - t0

try:
    import unicodedata
except ImportError:
    pass
else:
    class UnicodeProperties(Test):

        version = 2.0
        operations = 5 * 8
        inner_loops = 5 * 8

        def test(self, loops):

            data = (u'a', u'1', u' ', u'\u1234', u'\uFFFF')
            len_data = len(data)
            digit = unicodedata.digit
            numeric = unicodedata.numeric
            decimal = unicodedata.decimal
            category = unicodedata.category
            bidirectional = unicodedata.bidirectional
            decomposition = unicodedata.decomposition
            mirrored = unicodedata.mirrored
            combining = unicodedata.combining
            range_it = xrange(loops)
            t0 = perf.perf_counter()

            for i in range_it:

                c = data[i % len_data]

                digit(c, None)
                numeric(c, None)
                decimal(c, None)
                category(c)
                bidirectional(c)
                decomposition(c)
                mirrored(c)
                combining(c)

                digit(c, None)
                numeric(c, None)
                decimal(c, None)
                category(c)
                bidirectional(c)
                decomposition(c)
                mirrored(c)
                combining(c)

                digit(c, None)
                numeric(c, None)
                decimal(c, None)
                category(c)
                bidirectional(c)
                decomposition(c)
                mirrored(c)
                combining(c)

                digit(c, None)
                numeric(c, None)
                decimal(c, None)
                category(c)
                bidirectional(c)
                decomposition(c)
                mirrored(c)
                combining(c)

                digit(c, None)
                numeric(c, None)
                decimal(c, None)
                category(c)
                bidirectional(c)
                decomposition(c)
                mirrored(c)
                combining(c)

            return perf.perf_counter() - t0
