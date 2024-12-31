import os
import subprocess
import sys


class Shell:
    command = ""
    arguments = []
    debug = False

    def __init__(self):
        self.__handle()

    def __handle(self):
        """
        Main program loop.

        * write "$ " to stdout
        * read commands and arguments
        * handle commands
        * recursively loop until the program is exited (e.g. by calling
        self.exit())
        """
        self.__read_commands()
        self.__handle_commands()
        self.__handle()  # recursively loop until explicitly exited

    def __read_commands(self):
        """
        Read users commands and arguments.

        * Write "$ " to std out
        * Read user input
        * Split the input on " " to ['command', 'arg1', 'arg2', etc.]
        """
        self.__write_stdout("$ ", end_with_newline=False)
        commands = input()
        inputs = commands.split(" ")
        self.command = inputs[0]
        arguments = inputs[1:]
        self.arguments = self.__tokenise_args(arguments)
        if self.debug is True:
            self.__write_stdout(f"raw arguments = {arguments}")
            self.__write_stdout(f"tokenised arguments = {self.arguments}")

    @staticmethod
    def __tokenise_args(arguments: list) -> list:
        """
        Tokenise the input argument list.

        Combine multiple string arguments (list items) that are
        surrounded by a pair of single quotes into a single string.
        """
        tokenised_args = []
        quoted_arg = ''
        for i in range(len(arguments)):
            arg = arguments[i]
            if arg.startswith("'") and arg.endswith("'"):
                tokenised_args.append(arg[1:-1])
                continue
            if arg.startswith("'") and not arg.endswith("'"):
                quoted_arg += arg[1:]  # exclude starting single quote
                continue
            if arg == '':
                if quoted_arg != '':
                    quoted_arg += ' '
                continue
            if quoted_arg and not arg.endswith("'"):
                quoted_arg += f' {arg}'
                continue
            if arg.endswith("'") and not arg.startswith("'"):
                quoted_arg += f' {arg[:-1]}'  # exclude ending single quote
                tokenised_args.append(quoted_arg)
                quoted_arg = ''
                continue

            # else
            tokenised_args.append(arg)

        return tokenised_args

    def __handle_commands(self):
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
        if self.command == "debug_mode":
            if self.arguments[0].lower() in ["on", "true", "1"]:
                self.debug = True
                self.__write_stdout("Debug mode on")
            if self.arguments[0].lower() in ["off", "false", "0"]:
                self.debug = False
                self.__write_stdout("Debug mode off")
            return

        if hasattr(self, self.command):
            getattr(self, self.command)()
            return

        try:
            self.run_external_program()
        except ValueError:
            # could not find a valid filepath for the command in PATHS
            # environment variable
            self.__write_stdout(f"{self.command}: command not found")

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

    @staticmethod
    def __write_stdout(msg: str, end_with_newline=True):
        """
        Write the given message to stdout.
        """
        if end_with_newline:
            msg += '\n'
        sys.stdout.write(msg)
        sys.stdout.flush()

    def __one_arg_exactly(self):
        """
        Return True if there is exactly one argument given, else write
        an error message to stdout stating there were an invalid number
        of arguments then return False.

        :return: bool
        """
        if len(self.arguments) != 1:
            self.__write_stdout(
                f"{self.command}: invalid number of arguments"
            )
            return False

        return True

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

        if not self.__one_arg_exactly():
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
        self.__write_stdout(" ".join(self.arguments))

    def type(self):
        """
        Handle type commands.

        Write a string to stdout explaining if the given argument is
        a valid built-in command name, write the full path to the file
        if the file exists in a path from the PATHS environment
        variable, or write an error message explaining that the command
        could not be found.
        """
        if not self.__one_arg_exactly():
            return

        arg = self.arguments[0]
        if hasattr(self, arg):
            self.__write_stdout(f"{arg} is a shell builtin")
            return

        try:
            filepath = self.__get_path_for_file(arg)
            self.__write_stdout(f"{arg} is {filepath}")
        except ValueError:
            self.__write_stdout(f"{arg}: not found")

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
        self.__write_stdout(completed_process.stdout)

    def pwd(self):
        """
        Print the full path to the current working directory.

        This /should/ already be handled by self.run_external_program,
        for most systems/OSs, but on some (i.e. the CI server for
        CodeCrafters.io) `pwd` isn't locatable in any paths in the PATH
        environment variable so we'll handle it directly.
        """
        self.__write_stdout(f'{os.getcwd()}')

    def cd(self):
        """
        Handle requests to change the current working directory.
        """
        if not self.__one_arg_exactly():
            return

        arg = self.arguments[0]
        if "~" in arg:
            home_dir_path = os.environ.get("HOME")
            arg = arg.replace("~", home_dir_path)

        try:
            os.chdir(arg)
        except FileNotFoundError:
            self.__write_stdout(f"cd: {arg}: No such file or directory")


def main():
    Shell()


if __name__ == "__main__":
    main()
