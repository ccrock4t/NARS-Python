
"""
    Author: Christian Hahm
    Created: April 10, 2020
    Purpose: Program entry point
"""
import multiprocessing
import threading
import time

import Global
import InputChannel
import NARSGUI
import NARS


def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.

    """
    # First, create the NARS
    NARS_object = NARS.NARS()
    Global.Global.NARS = NARS_object
    experience_task_buffer_name = str(NARS_object.experience_task_buffer)
    experience_task_buffer_capacity = NARS_object.experience_task_buffer.capacity
    event_buffer_name = str(NARS_object.event_buffer)
    event_buffer_capacity = NARS_object.event_buffer.capacity
    memory_bag_name = str(NARS_object.memory.concepts_bag)
    memory_bag_capacity = NARS_object.memory.concepts_bag.capacity

    data_structure_names = (experience_task_buffer_name, event_buffer_name, memory_bag_name)
    data_structure_capacities = (experience_task_buffer_capacity, event_buffer_capacity, memory_bag_capacity)

    # multiprocess pipe to pass objects between NARS and GUI Processes
    pipe_gui_objects, pipe_NARS_objects = multiprocessing.Pipe() # 2-way object request pipe
    pipe_gui_strings, pipe_NARS_strings = multiprocessing.Pipe() # 1-way string pipe
    Global.Global.NARS_object_pipe = pipe_NARS_objects
    Global.Global.NARS_string_pipe = pipe_NARS_strings

    # setup internal/interface GUI
    if Global.Global.gui_use_internal_data or Global.Global.gui_use_interface:
        GUI_thread = multiprocessing.Process(target=NARSGUI.start_gui,
                                      args=(Global.Global.gui_use_internal_data,
                                            Global.Global.gui_use_interface,
                                            data_structure_names,
                                            data_structure_capacities,
                                            pipe_gui_objects,
                                            pipe_gui_strings),
                                      name="GUI thread",
                                      daemon=True)
        GUI_thread.start()
        while not pipe_NARS_objects.poll(1.0):
            print('Waiting for GUI Process to start')
        pipe_NARS_objects.recv() # received GUI ready signal

    # launch shell input thread
    shell_input_thread = threading.Thread(target=InputChannel.get_user_input,
                                           name="Shell input thread",
                                           daemon=True)
    shell_input_thread.start()

    Global.Global.set_paused(False)

    print('Starting NARS in the shell.')

    # Finally, run NARS in the shell
    Global.Global.NARS.memory.conceptualize_term(Global.Global.TERM_SELF)
    Global.Global.NARS.run()


if __name__ == "__main__":
    main()