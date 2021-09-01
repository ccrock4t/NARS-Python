import DataStructureTests
import GrammarTests
import InferenceEngineTests
import InferenceRuleTests
import Config


def main():
    DataStructureTests.main()
    GrammarTests.main()
    InferenceEngineTests.main()
    InferenceRuleTests.main()

if __name__ == "__main__":
    Config.DEBUG = False
    Config.GUI_USE_INTERFACE = False
    main()