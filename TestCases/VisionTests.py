import Config
import Global
import InputChannel
import NARS
import NALGrammar


from PIL import Image
import os
import threading

def supervised_learning_MNIST_0_or_1():
    #todo
    directory = 'supervised_learning/'
    train_dir_0 = directory + 'train_0'
    train_dir_1 = directory + 'train_1'
    test_dir_0 = directory + 'test_0'
    test_dir_1 = directory + 'test_1'

    """
        Training Phase
    """
    training_total = 0
    label_0 = '0'
    training_cycles = 20
    label_period = 4
    for root, dir, files, in os.walk(train_dir_0):
        total = training_cycles*len(files) / 100
        for file in files:
            img = Image.open(os.path.join(root,file))
            InputChannel.queue_visual_sensory_image_array(img)

            for i in range(training_cycles):
                Global.Global.NARS.do_working_cycle()
                if i % 4 == 0:
                    InputChannel.parse_and_queue_input_string("(" + label_0 + "--> SEEN). :|:")
                training_total += 1
                print('TRAINING DIGIT 0: ' + str(round(training_total / total, 2)) + "%")

    training_total = 0
    label_1 = '1'
    for root, dir, files, in os.walk(train_dir_1):
        total = training_cycles * len(files) / 100
        for file in files:
            img = Image.open(os.path.join(root,file))
            InputChannel.queue_visual_sensory_image_array(img)

            for i in range(training_cycles):
                Global.Global.NARS.do_working_cycle()
                if i % 4 == 0:
                    InputChannel.parse_and_queue_input_string("(" + label_1 + "--> SEEN). :|:")
                training_total += 1
                print('TRAINING DIGIT 1: ' + str(round(training_total / total, 2)) + "%")

    """
        Testing Phase
    """
    label = '0'
    correct = 0
    total = 0

    term_0_seen = NALGrammar.Terms.from_string("(" + label_0 + "--> SEEN)")
    term_1_seen = NALGrammar.Terms.from_string("(" + label_1 + "--> SEEN)")
    test_cycles = 20

    for root, dir, files, in os.walk(test_dir_0):
        for file in files:
            img = Image.open(os.path.join(root,file))
            InputChannel.queue_visual_sensory_image_array(img)
            for i in range(test_cycles):
                Global.Global.NARS.do_working_cycle()
                print('NARS is thinking...: ' + str(i) + '/' + str(test_cycles))
            exp_0 = Global.Global.NARS.memory.peek_concept(term_0_seen).belief_table.peek().get_expectation()
            exp_1 = Global.Global.NARS.memory.peek_concept(term_1_seen).belief_table.peek().get_expectation()

            if exp_0 > exp_1: # NARS thinks its a 0
                correct += 1

            total += 1
            print('Test Case Accuracy so far: ' + str(round(correct / total * 100, 2)) + "%")


    for root, dir, files, in os.walk(test_dir_1):
        for file in files:
            img = Image.open(os.path.join(root,file))
            InputChannel.queue_visual_sensory_image_array(img)
            for i in range(test_cycles):
                Global.Global.NARS.do_working_cycle()
                print('NARS is thinking...: ' + str(i) + '/' + str(test_cycles))

            exp_0 = Global.Global.NARS.memory.peek_concept(term_0_seen).belief_table.peek().get_expectation()
            exp_1 = Global.Global.NARS.memory.peek_concept(term_1_seen).belief_table.peek().get_expectation()

            if exp_1 > exp_0: # NARS thinks its a 1
                correct += 1
            total += 1
            print('Test Case Accuracy so far: ' + str(round(correct / total * 100,2)) + "%")


    print('======= TOTAL Test Case Accuracy: ' + str(round(correct / total * 100,2)) + "%")

def main():
    Config.GUI_USE_INTERFACE = False
    Config.SILENT_MODE = True
    Global.Global.NARS = NARS.NARS()
    Global.Global.set_paused(False)

    supervised_learning_MNIST_0_or_1()

if __name__ == "__main__":
    main()