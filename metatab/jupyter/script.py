# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Support for running notebooks converted to scripts
"""

import errno
import signal
import sys
import time
from subprocess import Popen, PIPE

from IPython.core import prefilter, magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.utils import py3compat
from IPython.utils.process import arg_split
from IPython.utils.text import DollarFormatter
from metatab.ipython import caller_locals
from os import system
from .magic import MetatabMagic
from IPython.core.magics.script import script_args

class ScriptIPython(object):
    """A Fake IPython object to supportin running some magics from converted scripts"""

    def __init__(self, user_ns):
        self.user_ns = user_ns
        self.mm = MetatabMagic(shell=self)
        pass

    def magic(self, arg_s):
        magic_name, _, magic_arg_s = arg_s.partition(' ')
        magic_name = magic_name.lstrip(prefilter.ESC_MAGIC)
        return self.run_line_magic(magic_name, magic_arg_s)

    def run_line_magic(self, magic_name, line):

        if hasattr(self.mm, magic_name):
            # Run any magics for metatab
            f = getattr(self.mm, magic_name)
            f(line)
            return

        elif magic_name == 'matplotlib':
            # Don't let matplotlib open a display window.
            import matplotlib
            matplotlib.use('AGG')


    def run_cell_magic(self, magic_name, line, cell):
        """Run a limited number of magics from scripts, without IPython"""

        if magic_name == 'bash':
            self.shebang("bash", cell)
        elif magic_name == 'metatab':
            self.mm.metatab(line, cell)


    # Stolen from IPython  distribution
    def system_piped(self, cmd):
        """Call the given cmd in a subprocess, piping stdout/err

        Parameters
        ----------
        cmd : str
          Command to execute (can not end in '&', as background processes are
          not supported.  Should not be a command that expects input
          other than simple text.
        """
        if cmd.rstrip().endswith('&'):
            # this is *far* from a rigorous test
            # We do not support backgrounding processes because we either use
            # pexpect or pipes to read from.  Users can always just call
            # os.system() or use ip.system=ip.system_raw
            # if they really want a background process.
            raise OSError("Background processes not supported.")

        # we explicitly do NOT return the subprocess status code, because
        # a non-None value would trigger :func:`sys.displayhook` calls.
        # Instead, we store the exit_code in user_ns.
        self.user_ns['_exit_code'] = system(self.var_expand(cmd, depth=1))

    # Stolen from IPython  distribution
    def var_expand(self, cmd, depth=0, formatter=DollarFormatter()):
        """Expand python variables in a string.

        The depth argument indicates how many frames above the caller should
        be walked to look for the local namespace where to expand variables.

        The global namespace for expansion is always the user's interactive
        namespace.
        """
        ns = self.user_ns.copy()
        try:
            frame = sys._getframe(depth + 1)
        except ValueError:
            # This is thrown if there aren't that many frames on the stack,
            # e.g. if a script called run_line_magic() directly.
            pass
        else:
            ns.update(frame.f_locals)

        try:
            # We have to use .vformat() here, because 'self' is a valid and common
            # name, and expanding **ns for .format() would make it collide with
            # the 'self' argument of the method.
            cmd = formatter.vformat(cmd, args=[], kwargs=ns)
        except Exception:
            # if formatter couldn't format, just let it go untransformed
            pass
        return cmd

    system = system_piped

    @magic_arguments.magic_arguments()
    @script_args
    @cell_magic("script")
    def shebang(self, line, cell):
        """Run a cell via a shell command

        The `%%script` line is like the #! line of script,
        specifying a program (bash, perl, ruby, etc.) with which to run.

        The rest of the cell is run by that program.

        Examples
        --------
        ::

            In [1]: %%script bash
               ...: for i in 1 2 3; do
               ...:   echo $i
               ...: done
            1
            2
            3
        """
        argv = arg_split(line, posix=not sys.platform.startswith('win'))
        args, cmd = self.shebang.parser.parse_known_args(argv)

        try:
            p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        except OSError as e:
            if e.errno == errno.ENOENT:
                print("Couldn't find program: %r" % cmd[0])
                return
            else:
                raise

        if not cell.endswith('\n'):
            cell += '\n'
        cell = cell.encode('utf8', 'replace')
        if args.bg:
            self.bg_processes.append(p)
            self._gc_bg_processes()
            if args.out:
                self.shell.user_ns[args.out] = p.stdout
            if args.err:
                self.shell.user_ns[args.err] = p.stderr
            self.job_manager.new(self._run_script, p, cell, daemon=True)
            if args.proc:
                self.shell.user_ns[args.proc] = p
            return

        try:
            out, err = p.communicate(cell)
        except KeyboardInterrupt:
            try:
                p.send_signal(signal.SIGINT)
                time.sleep(0.1)
                if p.poll() is not None:
                    print("Process is interrupted.")
                    return
                p.terminate()
                time.sleep(0.1)
                if p.poll() is not None:
                    print("Process is terminated.")
                    return
                p.kill()
                print("Process is killed.")
            except OSError:
                pass
            except Exception as e:
                print("Error while terminating subprocess (pid=%i): %s" \
                      % (p.pid, e))
            return
        out = py3compat.bytes_to_str(out)
        err = py3compat.bytes_to_str(err)
        if args.out:
            self.shell.user_ns[args.out] = out
        else:
            sys.stdout.write(out)
            sys.stdout.flush()
        if args.err:
            self.shell.user_ns[args.err] = err
        else:
            sys.stderr.write(err)
            sys.stderr.flush()

def get_ipython():
    return ScriptIPython(caller_locals())
