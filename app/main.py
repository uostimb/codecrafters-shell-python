import sys


class Shell:
    def __init__(self):
        self.command = ''
        self.arguments = []
        self.handle()

    def handle(self):
        self.read_command()
        self.handle_commands()

    def read_command(self):
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
        self.handle()

    def exit(self):
        if not self.arguments:
            exit(0)
        if len(self.arguments) == 1:
            exit(self.arguments[0])

        sys.stdout.write(f"{self.command}: invalid number of arguments\n")
        exit(0)


def main():
    Shell()


if __name__ == "__main__":
    main()
