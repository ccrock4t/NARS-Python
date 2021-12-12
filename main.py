
"""
    Author: Christian Hahm
    Created: April 10, 2020
    Purpose: Program entry point
"""



import threading
import multiprocessing
import Config

import Global
import InputChannel
import NARSGUI
import NARS



class GUIProcess(multiprocessing.Process):
    def __init__(self):
        NARS_object: NARS = Global.Global.NARS
        narsese_buffer_ID = (str(NARS_object.narsese_buffer), type(NARS_object.narsese_buffer).__name__)
        narsese_buffer_capacity = NARS_object.narsese_buffer.capacity
        vision_buffer_ID = (str(NARS_object.vision_buffer), type(NARS_object.narsese_buffer).__name__)
        vision_buffer_dims = str(NARS_object.vision_buffer.array.shape)
        temporal_module_ID = (str(NARS_object.temporal_module), type(NARS_object.temporal_module).__name__)
        temporal_module_capacity = NARS_object.temporal_module.capacity
        memory_bag_ID = (str(NARS_object.memory.concepts_bag), type(NARS_object.memory.concepts_bag).__name__)
        memory_bag_capacity = NARS_object.memory.concepts_bag.capacity

        data_structure_IDs = (narsese_buffer_ID, vision_buffer_ID, temporal_module_ID, memory_bag_ID)
        data_structure_capacities = (narsese_buffer_capacity, vision_buffer_dims, temporal_module_capacity, memory_bag_capacity)

        # multiprocess pipe to pass objects between NARS and GUI Processes
        pipe_gui_objects, pipe_NARS_objects = multiprocessing.Pipe()  # 2-way object request pipe
        pipe_gui_strings, pipe_NARS_strings = multiprocessing.Pipe()  # 1-way string pipe
        Global.Global.NARS_object_pipe = pipe_NARS_objects
        Global.Global.NARS_string_pipe = pipe_NARS_strings

        multiprocessing.Process.__init__(self,target=NARSGUI.start_gui,
                             args=(Config.GUI_USE_INTERFACE,
                                   data_structure_IDs,
                                   data_structure_capacities,
                                   pipe_gui_objects,
                                   pipe_gui_strings),
                             name="GUI thread",
                             daemon=True)
        self.start()

        while not pipe_NARS_objects.poll(1.0):
            print('Waiting for GUI Process to start')
        pipe_NARS_objects.recv()  # received GUI ready signal



def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.

    """

    # First, create the NARS
    NARS_object = NARS.NARS()
    Global.Global.NARS = NARS_object

    # setup internal/interface GUI
    if Config.GUI_USE_INTERFACE:
        GUIProcess()

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
    # On Windows calling this function is necessary.
    # On Linux/OSX it does nothing.
    multiprocessing.freeze_support()
    main()