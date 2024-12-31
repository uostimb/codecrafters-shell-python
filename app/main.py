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
    stdout_output = ""
    stderr_output = ""
    filename_to_write_stdout = ""
    filename_to_write_stderr = ""

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
        if not self.command == "":
            self._handle_commands()
            self._write_output()
        self._handle()  # recursively loop until explicitly exited

    def _read_commands(self):
        """
        Read users commands and arguments.

        * Write "$ " to std out
        * Read user input
        * Split the input on " " to ['command', 'arg1', 'arg2', etc.]
          gracefully handling single and double quotes in strings.
        * Handle redirecting stdout and stderr to files if required.
        """
        self._write_msg("$ ")
        commands = input()
        if not commands:
            return
        inputs = shlex.split(commands, posix=True)  # This feels like a cop-out
        self.command = inputs[0]
        self.arguments = inputs[1:]
        self._set_up_file_redirection()

    def _set_up_file_redirection(self):
        """
        Setup redirecting stdout and stderr to a file.

        Remove the redirection-related items from self.arguments
        """
        self.filename_to_write_stdout = ""
        self.filename_to_write_stderr = ""
        arg_indexes_to_pop = []
        for i in range(len(self.arguments)):
            arg = self.arguments[i]
            for redirect_arg, filename_var in (
                (">",  "filename_to_write_stdout"),
                ("1>", "filename_to_write_stdout"),
                ("2>", "filename_to_write_stderr"),
            ):
                if arg == redirect_arg:
                    filename = self.arguments[i+1]
                    setattr(self, filename_var, filename)
                    # clear/create file if required
                    open(filename, 'w').close()
                    arg_indexes_to_pop.append(i)
                    arg_indexes_to_pop.append(i+1)


        arg_indexes_to_pop.sort(reverse=True)
        for i in arg_indexes_to_pop:
            self.arguments.pop(i)

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
        self.stdout_output = ""
        self.stderr_output = ""

        if self.command in self.builtins:
            getattr(self, self.command)()
            return

        try:
            self.run_external_program()
        except ValueError:
            # could not find a builtin with that name or a valid
            # filepath in the PATHS environment variable for a program
            # with that name
            self.stderr_output = f"{self.command}: command not found\n"

    def _write_output(self):
        """
        Write the results of the given command if required.

        Write the outputs from self.stdout_output and self.stderr_output
        to the required file if a filename was specified, otherwise
        write them to stdout and/or stderr.
        """
        for filename, output, std_type in (
            (self.filename_to_write_stdout, self.stdout_output, sys.stdout),
            (self.filename_to_write_stderr, self.stderr_output, sys.stderr),
        ):
            if not output:
                # Nothing to write
                continue

            if not filename:
                # Write to shell
                self._write_msg(output, std_type)
                continue

            # Write to file
            with open(filename, "w") as file:
                file.write(output)

    @staticmethod
    def _write_msg(msg: str, std_type=sys.stdout):
        """
        Write the given message to the given std type.

        :param msg: message to write
        :param std_type: one of sys.stdout or sys.stderr
        """
        std_type.write(msg)
        std_type.flush()

    def _one_arg_exactly(self):
        """
        Return True if there is exactly one argument given, else write
        an error message to stdout stating there were an invalid number
        of arguments then return False.

        :return: bool
        """
        if len(self.arguments) != 1:
            self._write_msg(
                f"{self.command}: invalid number of arguments\n",
                sys.stderr,
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

        Return the given arguments as-is to stdout.
        """
        self.stdout_output = f"{' '.join(self.arguments)}\n"

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
            self.stdout_output = f"{arg} is a shell builtin\n"
            return

        try:
            filepath = self._get_path_for_file(arg)
            self.stdout_output = f"{arg} is {filepath}\n"
        except ValueError:
            self.stderr_output = f"{arg}: not found\n"

    def pwd(self):
        """
        Print the full path to the current working directory.

        This /should/ already be handled by self.run_external_program,
        for most systems/OSs, but on some (i.e. the CI server for
        CodeCrafters.io) `pwd` isn't locatable in any paths in the PATH
        environment variable so we'll handle it directly.
        """
        self.stdout_output = f'{os.getcwd()}\n'

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
            self.stderr_output = f"cd: {arg}: No such file or directory\n"

    def run_external_program(self):
        """
        Handle running external programs as a subprocess.

        Attempt to locate the given command as a program in paths from
        the PATHS environment variable and run it with the given
        arguments.
        """
        # will raise ValueError if no valid filepath exists
        filepath = self._get_path_for_file(self.command)

        to_run = [filepath] + self.arguments
        completed_process = subprocess.run(
            to_run,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.stderr_output = completed_process.stderr
        self.stdout_output = completed_process.stdout


def main():
    Shell()


if __name__ == "__main__":
    main()
