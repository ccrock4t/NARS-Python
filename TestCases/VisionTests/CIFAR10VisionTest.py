from keras.datasets import cifar10

from TestCases.VisionTests.GenericVisionTest import GenericVisionTest

if __name__ == "__main__":
    vision_test = GenericVisionTest(dataset_loader=cifar10,
                                    gui_enabled=True,
                                    train_size=10,
                                    test_size=10,
                                    training_cycles=1000)
    vision_test.run_main_test()