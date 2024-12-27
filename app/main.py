import sys


def main():
    sys.stdout.write("$ ")

    # Wait for user input
    command = input()

    # If `command` isn't a valid value, return an error message
    sys.stdout.write(f"{command}: command not found\n")


if __name__ == "__main__":
    main()
