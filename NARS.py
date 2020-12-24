import InputBuffer
from NARSMemory import Memory
import Globals
import threading
import os


def main():
    Globals.memory = Memory()

    t = threading.Thread(target=get_user_input, name="user input thread")
    t.daemon = True
    t.start()

    while True:
        do_inference_cycle()

def do_inference_cycle():

    item = Globals.memory.concepts_bag.get()

    if item is None:
        return

    print(item.object.get_formatted_string())

    Globals.memory.concepts_bag.put(item)


def get_user_input():
    userinput = ""

    while userinput != "exit":
        userinput = input("")
        if userinput == "count":
            print(Globals.memory.concepts_bag.count)
        else:
            InputBuffer.add_input(userinput)

    os._exit()

if __name__ == "__main__":
    main()