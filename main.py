
"""
    Author: Christian Hahm
    Created: April 10, 2020
    Purpose: Program entry point
"""
import threading
import time

import Global
import NARSGUI
import NARS


def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.
    """
    # set globals
    Global.Global.gui_use_internal_data = True  # Setting this to False will prevent creation of the Internal Data GUI thread
    # todo investigate why using the interface slows down the system
    Global.Global.gui_use_interface = False # Setting this to False uses the shell as interface, and results in a massive speedup

    # First, create the NARS
    Global.Global.NARS = NARS.NARS()

    # setup internal/interface GUI
    if Global.Global.gui_use_internal_data or Global.Global.gui_use_interface:
        GUI_thread = threading.Thread(target=NARSGUI.NARSGUI.execute_gui, name="GUI thread", daemon=True)
        GUI_thread.daemon = True
        GUI_thread.start()
        while not Global.Global.gui_thread_ready:
            print('Waiting for GUI thread...')
            time.sleep(1.0)
            if not Global.Global.gui_use_interface:
                # launch shell input thread
                shell_input_thread = threading.Thread(target=NARSGUI.NARSGUI.get_user_input, name="Shell input thread",
                                                      daemon=True)
                shell_input_thread.daemon = True
                shell_input_thread.start()
                while not Global.Global.input_thread_ready:
                    print('Waiting for input thread...')
                    time.sleep(1.0)

    Global.Global.paused = Global.Global.gui_use_interface

    # Finally, run NARS in the shell
    Global.Global.NARS.run()

if __name__ == "__main__":
    main()