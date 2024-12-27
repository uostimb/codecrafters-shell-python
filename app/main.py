import sys


class Shell:
    command = ''
    arguments = []

    def __init__(self):
        self.handle()

    def handle(self):
        self.reset()
        self.read_commands()
        self.handle_commands()

    def reset(self):
        self.command = ''
        self.arguments = []

    def read_commands(self):
        sys.stdout.write("$ ")
        commands = input()
        inputs = commands.split(" ")
        self.command = inputs[0]
        if len(inputs) > 1:
            self.arguments = inputs[1:]

    def handle_commands(self):
        if hasattr(self, self.command):
            getattr(self, self.command)()
        else:
            sys.stdout.write(f"{self.command}: command not found\n")
            sys.stdout.flush()
        self.handle()

    def exit(self):
        if not self.arguments:
            sys.stdout.write("calling sys.exit(0)\n")
            sys.stdout.flush()
            sys.exit(0)
        if len(self.arguments) == 1:
            argument = self.arguments[0]
            sys.stdout.write(f"calling sys.exit({argument})\n")
            sys.stdout.flush()
            sys.exit(argument)

        sys.stdout.write(f"{self.command}: invalid number of arguments\n")
        sys.stdout.write("calling sys.exit(0)\n")
        sys.stdout.flush()
        sys.exit(0)


def main():
    Shell()


if __name__ == "__main__":
    main()
