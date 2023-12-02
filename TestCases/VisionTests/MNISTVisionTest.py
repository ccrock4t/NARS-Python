from keras.datasets import mnist

from TestCases.VisionTests.GenericVisionTest import GenericVisionTest

if __name__ == "__main__":
    vision_test = GenericVisionTest(dataset_loader=mnist,
                                    gui_enabled=True,
                                    train_size=100,
                                    test_size=10,
                                    training_cycles=5)
    vision_test.run_main_test()