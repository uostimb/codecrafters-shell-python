import os
import subprocess
import sys


class Shell:
    command = ''
    arguments = []

    def __init__(self):
        self.__handle()

    def __handle(self):
        """
        Main program loop.

        * Resets internal memory to initial state (to prevent reuse of
        prior arguments)
        * read commands and arguments
        * cast numeric integer-string arguments to ints
        * handle users commands
        * recursively calls self

        Will recursively loop until the program is exited (e.g. by
        calling self.exit())
        """
        self.__reset()
        self.__read_commands()
        self.__handle_commands()
        self.__handle()  # recursively loop until explicitly exited

    def __reset(self):
        """
        Reset self.command and self.arguments to initial state.
        """
        self.command = ''
        self.arguments = []

    def __read_commands(self):
        """
        Read users commands and arguments.

        * Write "$ " to std out
        * Read user input
        * Split the input on " " to ['command', 'arg 1', 'arg 2', ...]
        """
        sys.stdout.write("$ ")
        commands = input()
        inputs = commands.split(" ")
        self.command = inputs[0]
        self.arguments = inputs[1:]

    def __handle_commands(self):
        """
        Handle command in self.command

        If the given command name matches an attribute (method name) on
        self then call that method.

        If the given command name doesn't match any attributes (method
        names) on self then try to interpret the command as a request to
        run an external program (from paths on the PATHS environment
        variable).

        If the command does not match a valid method name or a valid
        file path then write an error message to stdout.
        """
        if hasattr(self, self.command):
            getattr(self, self.command)()
            return

        try:
            self.run_external_program()
        except ValueError:
            # could not find a valid filepath for the command in PATHS
            # environment variable
            sys.stdout.write(f"{self.command}: command not found\n")
            sys.stdout.flush()

    @staticmethod
    def __get_path_for_file(filename: str):
        """
        Check if filename is in any path from PATHs environment var.

        Return the full filepath of the file from the first path that
         contains it, or raise ValueError the filename is not contained
         in any path.

        :param filename: string
        :return: str
        """
        paths = os.environ.get("PATH").split(":")
        for path in paths:
            filepath = os.path.join(path, filename)
            if os.path.isfile(filepath):
                return filepath

        raise ValueError(
            f"{filename} not found in any path from PATHS environment"
            " variable."
        )

    def exit(self):
        """
        Handle exit commands.

        If no arguments were passed to the exit command then exit the
        application with exit code 0 (the default for sys.exit()).

        If a single integer argument was passed to the exit command then
        exit the application using the argument as the exit code.

        If multiple arguments were passed to the exit command, write an
        error message to stdout.
        """
        if not self.arguments:
            sys.exit()

        if len(self.arguments) > 1:
            sys.stdout.write(f"{self.command}: invalid number of arguments\n")
            sys.stdout.flush()
            return

        argument = self.arguments[0]
        if isinstance(argument, str) and argument.isdigit():
            argument = int(argument)
        sys.exit(argument)

    def echo(self):
        """
        Handle echo commands.

        Write any given arguments to stdout.
        """
        str_to_write = " ".join(self.arguments)
        str_to_write += "\n"
        sys.stdout.write(str_to_write)
        sys.stdout.flush()

    def type(self):
        """
        Handle type commands.

        Write a string to stdout explaining if the given argument is
        a valid or invalid built-in command name.
        """
        if len(self.arguments) != 1:
            sys.stdout.write(
                f"{self.command}: invalid number of arguments\n"
            )
            sys.stdout.flush()
            return

        arg = self.arguments[0]
        if hasattr(self, arg):
            sys.stdout.write(f"{arg} is a shell builtin\n")
            sys.stdout.flush()
            return

        try:
            filepath = self.__get_path_for_file(arg)
            sys.stdout.write(f"{arg} is {filepath}\n")
        except ValueError:
            sys.stdout.write(f"{arg}: not found\n")
        finally:
            sys.stdout.flush()

    def run_external_program(self):
        """
        Handle running external programs as a subprocess.

        Attempt to locate the given command as a program in paths from
        the PATHS environment variable and run it with the given
        arguments, then print any return from both stdout and stderr to
        stdout.
        """
        # will raise ValueError if no valid filepath exists
        filepath = self.__get_path_for_file(self.command)

        to_run = [filepath] + self.arguments
        completed_process = subprocess.run(
            to_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        sys.stdout.write(completed_process.stdout)
        sys.stdout.flush()

    @staticmethod
    def pwd():
        """
        Print the full path to the current working directory.

        This /should/ already be handled by self.run_external_program,
        but on some systems (i.e. the CI server for CodeCrafters.io)
        `pwd` isn't locatable in any paths in the PATH environment
        variable and must be assumed to be handled directly by the
        underlying shell/OS.
        """
        completed_process = subprocess.run(
            'pwd',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        sys.stdout.write(completed_process.stdout)
        sys.stdout.flush()


def main():
    Shell()


if __name__ == "__main__":
    main()
