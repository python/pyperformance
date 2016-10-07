""" CommandLine - Get and parse command line options

    NOTE: This still is very much work in progress !!!

    Different version are likely to be incompatible.

    TODO:

    * Incorporate the changes made by (see Inbox)
    * Add number range option using srange()

"""

from __future__ import print_function

__copyright__ = """\
Copyright (c), 1997-2006, Marc-Andre Lemburg (mal@lemburg.com)
Copyright (c), 2000-2006, eGenix.com Software GmbH (info@egenix.com)
See the documentation for further information on copyrights,
or contact the author. All Rights Reserved.
"""
__version__ = '1.2'

# Application baseclass


class Application:

    """ Command line application interface with builtin argument
        parsing.

    """
    # Options the program accepts (Option instances)
    options = []

    # The help layout looks like this:
    # [header]   - defaults to ''
    #
    # options:
    # [options]  - formatted from self.options
    #
    # Note: all fields that do not behave as template are formatted
    #       using the instances dictionary as substitution namespace,
    #       e.g. %(name)s will be replaced by the applications name.
    #

    # Header (default to program name)
    header = ''

    # Name (defaults to program name)
    name = ''

    # Copyright to show
    copyright = __copyright__

    # Generate debug output ?
    debug = 0

    # Generate verbose output ?
    verbose = 0

    def __init__(self):
        # Start Application
        rc = 0
        try:
            # Start application
            rc = self.main()
            if rc is None:
                rc = 0

        except SystemExit as rcException:
            rc = rcException.code

        except KeyboardInterrupt:
            print()
            print('* User Break')
            print()
            rc = 1

        raise SystemExit(rc)

    def exit(self, rc=0):
        """ Exit the program.

            rc is used as exit code and passed back to the calling
            program. It defaults to 0 which usually means: OK.

        """
        raise SystemExit(rc)

    def print_header(self):

        print('-' * 72)
        print(self.header % self.__dict__)
        print('-' * 72)
        print()

    # Handlers for long options have two underscores in their name

    def handle__copyright(self, arg):

        self.print_header()
        copyright = self.copyright % self.__dict__
        print(copyright.strip())
        print()
        return 0

    def main(self):
        """ Override this method as program entry point.

            The return value is passed to sys.exit() as argument.  If
            it is None, 0 is assumed (meaning OK). Unhandled
            exceptions are reported with exit status code 1 (see
            __init__ for further details).

        """
        return None
