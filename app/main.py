import os
import shlex
import subprocess
import sys


class Shell:
    command = ""
    arguments = []
    builtins = [
        "exit",
        "echo",
        "type",
        "pwd",
        "cd",
    ]
    debug = False
    output = ""
    write_to_filename = ""

    def __init__(self):
        self._handle()

    def _handle(self):
        """
        Main program loop.

        * write "$ " to stdout
        * read commands and arguments
        * handle commands
        * recursively loop until the program is exited (e.g. by calling
        self.exit())
        """
        self._read_commands()
        self._handle_commands()
        self._write_output()
        self._handle()  # recursively loop until explicitly exited

    def _read_commands(self):
        """
        Read users commands and arguments.

        * Write "$ " to std out
        * Read user input
        * Split the input on " " to ['command', 'arg1', 'arg2', etc.]
        """
        self._write_stdout("$ ")
        commands = input()
        inputs = shlex.split(commands, posix=True)  # This feels like a cop-out
        self.command = inputs[0]
        self.arguments = inputs[1:]
        if self.debug is True:
            self._write_stdout(f"tokenised arguments = {self.arguments}\n")

        # setup outputting results to a file if required
        self.write_to_filename = ''
        for i in range(len(self.arguments)):
            arg = self.arguments[i]
            if arg in ['>', '1>']:
                self.write_to_filename = self.arguments[i+1]
                self.arguments = self.arguments[:i]
                break

    def _handle_commands(self):
        """
        Handle the given command.

        If the given command name matches a method name then call that
        method.

        If the given command name doesn't match any method names
        then try to interpret the command as a request to
        run an external program (from paths on the PATHS environment
        variable).

        If the command does not match a valid method name or a valid
        file path then write an error message to stdout.
        """
        self.output = ""
        if self.command == "debug_mode":
            if self.arguments:
                if self.arguments[0].lower() in ["on", "true", "1"]:
                    self.debug = True
                if self.arguments[0].lower() in ["off", "false", "0"]:
                    self.debug = False
            self._write_stdout(f"Debug mode: {self.debug}\n")
            return

        if self.command in self.builtins:
            self.output = getattr(self, self.command)()
            return

        try:
            self.output = self.run_external_program()
        except ValueError:
            # could not find a builtin with that name or a valid
            # filepath in the PATHS environment variable for a program
            # with that name
            self._write_stdout(f"{self.command}: command not found\n")

    def _write_output(self):
        """
        Write the results of the given command.

        Write the output (from self.output) to the required file,
        otherwise write it to stdout.
        """
        if not self.output:
            return

        if self.write_to_filename:
            with open(self.write_to_filename, 'w') as file:
                file.write(self.output)
            if self.debug is True:
                escaped_output = (
                    self.output
                    .encode("unicode_escape")
                    .decode("utf-8")
                )
                escaped_filename = (
                    self.write_to_filename
                    .encode("unicode_escape")
                    .decode("utf-8")
                )
                self._write_stdout(
                    f'Wrote "{escaped_output}" to file '
                    f'"{escaped_filename}"\n'
                )
            return

        self._write_stdout(self.output)

    @staticmethod
    def _write_stdout(msg: str):
        """
        Write the given message to stdout.
        """
        sys.stdout.write(msg)
        sys.stdout.flush()

    def _one_arg_exactly(self):
        """
        Return True if there is exactly one argument given, else write
        an error message to stdout stating there were an invalid number
        of arguments then return False.

        :return: bool
        """
        if len(self.arguments) != 1:
            self._write_stdout(
                f"{self.command}: invalid number of arguments\n"
            )
            return False

        return True

    @staticmethod
    def _get_path_for_file(filename: str):
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
            sys.exit()  # default exit code 0

        if not self._one_arg_exactly():
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
        return f"{' '.join(self.arguments)}\n"

    def type(self):
        """
        Handle type commands.

        Write a string to stdout explaining if the given argument is
        a valid built-in command name, write the full path to the file
        if the file exists in a path from the PATHS environment
        variable, or write an error message explaining that the command
        could not be found.
        """
        if not self._one_arg_exactly():
            return

        arg = self.arguments[0]
        if arg in self.builtins:
            return f"{arg} is a shell builtin\n"

        try:
            filepath = self._get_path_for_file(arg)
            return f"{arg} is {filepath}\n"
        except ValueError:
            return f"{arg}: not found\n"

    @staticmethod
    def pwd():
        """
        Print the full path to the current working directory.

        This /should/ already be handled by self.run_external_program,
        for most systems/OSs, but on some (i.e. the CI server for
        CodeCrafters.io) `pwd` isn't locatable in any paths in the PATH
        environment variable so we'll handle it directly.
        """
        return f'{os.getcwd()}\n'

    def cd(self):
        """
        Handle requests to change the current working directory.
        """
        if not self._one_arg_exactly():
            return

        arg = self.arguments[0]
        if "~" in arg:
            home_dir_path = os.environ.get("HOME")
            arg = arg.replace("~", home_dir_path)

        try:
            os.chdir(arg)
        except FileNotFoundError:
            return f"cd: {arg}: No such file or directory\n"

    def run_external_program(self):
        """
        Handle running external programs as a subprocess.

        Attempt to locate the given command as a program in paths from
        the PATHS environment variable and run it with the given
        arguments, then print any return from both stdout and stderr to
        stdout.
        """
        # will raise ValueError if no valid filepath exists
        filepath = self._get_path_for_file(self.command)

        to_run = [filepath] + self.arguments
        completed_process = subprocess.run(
            to_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return completed_process.stdout


def main():
    Shell()


if __name__ == "__main__":
    main()
