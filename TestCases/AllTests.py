import Config
import DataStructureTests
import Global
import GrammarTests
import InferenceEngineTests
import InferenceRuleTests

def main():
    DataStructureTests.main()
    GrammarTests.main()
    InferenceEngineTests.main()
    InferenceRuleTests.main()

if __name__ == "__main__":
    Config.gui_use_interface = False
    main()