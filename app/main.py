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
        * Read users input
        * Split the input on " " to [[command], [arguments, ...]]"
        * Cast any integer string arguments to ints
        """
        sys.stdout.write("$ ")
        commands = input()
        inputs = commands.split(" ")
        self.command = inputs[0]
        arguments = inputs[1:]
        # Cast str integer arguments to ints
        for arg in arguments:
            if isinstance(arg, str) and arg.isdigit():
                self.arguments.append(int(arg))
            else:
                self.arguments.append(arg)

    def __handle_commands(self):
        """
        Handle command in self.command

        If the given command name matches an attribute (method name) on
        self then call that method.

        If the given command name doesn't match any attributes (method
        names) on self then write an error message to stdout.
        """
        if hasattr(self, self.command):
            getattr(self, self.command)()
        else:
            sys.stdout.write(f"{self.command}: command not found\n")
            sys.stdout.flush()

    def exit(self):
        """
        Handle exit commands.

        If no arguments were passed to the exit command then exit the
        application with exit code 0.

        If a single argument was passed to the exit command then exit
        the application using the argument as the exit code.

        If multiple arguments were passed to the exit command, write an
        error message to stdout and then exit with exit code 1.
        """
        if not self.arguments:
            sys.exit()
        if len(self.arguments) == 1:
            argument = self.arguments[0]
            sys.exit(argument)

        sys.stdout.write(f"{self.command}: invalid number of arguments\n")
        sys.stdout.flush()
        sys.exit(1)

    def echo(self):
        """
        Handle echo commands.

        Simply write any given arguments to stdout.
        """
        str_to_write = " ".join(self.arguments)
        str_to_write += '\n'
        sys.stdout.write(str_to_write)
        sys.stdout.flush()


def main():
    Shell()


if __name__ == "__main__":
    main()
