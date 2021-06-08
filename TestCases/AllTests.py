import DataStructureTests
import Global
import GrammarTests
import InferenceEngineTests

def main():
    DataStructureTests.main()
    GrammarTests.main()
    InferenceEngineTests.main()

if __name__ == "__main__":
    Global.Global.gui_use_internal_data = False
    Global.Global.gui_use_interface = False
    main()