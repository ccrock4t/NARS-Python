
"""
    Author: Christian Hahm
    Created: April 10, 2020
    Purpose: Program entry point
"""



import os
import sys
import threading
import multiprocessing
# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

import Global
import InputChannel
import NARSGUI
import NARS


if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen


class GUIProcess(multiprocessing.Process):
    def __init__(self):
        NARS_object = Global.Global.NARS
        global_task_buffer_ID = ("nullid", "buffer")
        global_task_buffer_capacity = 0
        event_buffer_ID = (str(NARS_object.event_buffer), type(NARS_object.event_buffer).__name__)
        event_buffer_capacity = NARS_object.event_buffer.capacity
        memory_bag_ID = (str(NARS_object.memory.concepts_bag), type(NARS_object.memory.concepts_bag).__name__)
        memory_bag_capacity = NARS_object.memory.concepts_bag.capacity

        data_structure_IDs = (global_task_buffer_ID, event_buffer_ID, memory_bag_ID)
        data_structure_capacities = (global_task_buffer_capacity, event_buffer_capacity, memory_bag_capacity)

        # multiprocess pipe to pass objects between NARS and GUI Processes
        pipe_gui_objects, pipe_NARS_objects = multiprocessing.Pipe()  # 2-way object request pipe
        pipe_gui_strings, pipe_NARS_strings = multiprocessing.Pipe()  # 1-way string pipe
        Global.Global.NARS_object_pipe = pipe_NARS_objects
        Global.Global.NARS_string_pipe = pipe_NARS_strings

        multiprocessing.Process.__init__(self,target=NARSGUI.start_gui,
                             args=(Global.Global.gui_use_internal_data,
                                   Global.Global.gui_use_interface,
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
    # On Windows calling this function is necessary.
    # On Linux/OSX it does nothing.
    multiprocessing.freeze_support()

    # First, create the NARS
    NARS_object = NARS.NARS()
    Global.Global.NARS = NARS_object

    # setup internal/interface GUI
    if Global.Global.gui_use_internal_data or Global.Global.gui_use_interface:
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
    main()