import InputBuffer
from NARSMemory import Memory
import Globals

def main():
    Globals.memory = Memory()
    userinput = ""

    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input(userinput)


if __name__ == "__main__":
    main()