import glob
import threading
import time
from operator import add

import NALInferenceRules

import numpy as np

import Config
import Global
import InputChannel
import NARS
import NALGrammar


from PIL import Image, ImageTk
import os
import tkinter as tk


directory = 'supervised_learning/'
dir_0 = directory + '0/'
dir_1 = directory + '1/'

digit_to_label = {}
digit_to_detected_term = {}
for i in range(0,10):
    term_str = "(" + str(i) + " --> SEEN)"
    term = NALGrammar.Terms.from_string(term_str)
    digit_to_label[i] = term_str + ". :|: %1.0;0.99%"
    digit_to_detected_term[i] = term

digit_to_goal_op_term = {}
for i in range(10):
    term_str = "((*,{SELF}) --> press_digit_" + str(i) + ")"
    term = NALGrammar.Terms.from_string(term_str)
    digit_to_goal_op_term[i] = term

def break_time(duration,clear_img=False):
    # give the system a small break
    global_gui.update_test_buttons(-1)
    if clear_img:
        Global.Global.NARS.vision_buffer.clear()
        global_gui.clear_visual_image()
        global_gui.set_visual_image(Image.fromarray(Global.Global.NARS.vision_buffer.img))
    global_gui.set_status_label('BREAK TIME...')
    for i in range(duration):
        Global.Global.NARS.do_working_cycle()
        global_gui.set_status_label('BREAK:\ncycle ' + str(i) + ' / ' + str(duration) \
                                       + '\n' + str(round(i* 100 / duration, 2)) + "%")
        global_gui.update_sliders()

def seed_digit_goals():
    """
    Seed goals to identify digits 0 through 9
    :return:
    """
    for i in range(10):
        label = "(&/,(" + str(i) + " --> SEEN),((*,{SELF}) --> press_digit_" + str(i) + "))! %1.0;0.99%"
        InputChannel.parse_and_queue_input_string(label)
        Global.Global.NARS.do_working_cycle()

def seed_bit_goals():
    """
    Seed goals to identify 0 and 1
    :return:
    """
    for i in range(2):
        label = "(&/,(" + str(i) + " --> SEEN),((*,{SELF}) --> press_digit_" + str(i) + "))! %1.0;0.99%"
        InputChannel.parse_and_queue_input_string(label)
        Global.Global.NARS.do_working_cycle()

def supervised_learning_0_or_1_one_example():
    training_cycles = 500
    testing_cycles = 500
    break_duration = 250

    img_0 = Image.open(dir_0 + "/" + os.listdir(dir_0)[0])
    img_1 = Image.open(dir_1 + "/" + os.listdir(dir_1)[0])

    """
        Training Phase
    """
    train(x_train=[np.array(img_0), np.array(img_1)],
          y_train=[0, 1],
          cycles=training_cycles)


    """
        Testing Phase
    """
    test(bit=True,
         x_test=[np.array(img_0), np.array(img_1)],
         y_test=[0,1],
         cycles=testing_cycles,
         break_duration=break_duration)


def supervised_learning_MNIST_0_or_1_dataset():
    training_cycles = 1000
    testing_cycles = 500
    break_duration = 100

    """
        Training Phase
    """
    x_fname_list = glob.glob(dir_0 + "*.png")
    y_list = [0] * len(x_fname_list)
    x_fname_list += (glob.glob(dir_1 + "*.png"))
    y_list += ([1] * (len(x_fname_list) - len(y_list)))

    x_list = []
    for fname in x_fname_list:
        x_list.append(np.array(Image.open(fname)))
    x_list = np.array(x_list)
    y_list = np.array(y_list)

    assert len(x_list) == len(y_list)
    p = np.random.permutation(len(x_list))
    x_list, y_list = x_list[p], y_list[p]

    # shorten to desired length
    length = 100
    x_list = x_list[0:length]
    y_list = y_list[0:length]

    percent_of_test_img = 0.3
    cutoff = round(percent_of_test_img*len(x_list))
    x_test, y_test = x_list[0:cutoff], y_list[0:cutoff]
    x_train, y_train = x_list[cutoff:], y_list[cutoff:]


    train(x_train=x_train,
          y_train=y_train,
          cycles=training_cycles)


    """
        Testing Phase
    """
    test(True,
         x_test=x_test,
         y_test=y_test,
         cycles=testing_cycles,
         break_duration=break_duration)

def supervised_learning_MNIST():
    gui = MNISTVisionTestGUI()
    thread = threading.Thread(target=gui.start, daemon=True)
    thread.start()

    """
        Training Phase
    """
    training_total = 0
    training_cycles = 200
    testing_cycles = 250
    break_duration = 25

    file_num = 0

    x_list = []
    y_list = []
    digit_folder_list = glob.glob(directory + '*')
    for folder_name in digit_folder_list:
        digit = int(folder_name[-1])
        x_fname_list = glob.glob(folder_name + "/*.png")
        y_list += [digit] * len(x_fname_list)

        for fname in x_fname_list:
            x_list.append(np.array(Image.open(fname)))

    x_list = np.array(x_list)
    y_list = np.array(y_list)

    assert len(x_list) == len(y_list)
    p = np.random.permutation(len(x_list))
    x_list, y_list = x_list[p], y_list[p]

    # shorten to desired length
    length = 225
    x_list = x_list[0:length]
    y_list = y_list[0:length]

    percent_of_train_img = 0.8
    cutoff = round(percent_of_train_img*len(x_list))
    x_train, y_train = x_list[0:cutoff], y_list[0:cutoff]
    x_test, y_test = x_list[cutoff:], y_list[cutoff:]

    train(x_train=x_train,
          y_train=y_train,
          cycles=training_cycles)

    """
        Testing Phase
    """


class MNISTVisionTestGUI:
    ZOOM = 16

    def start(self):
        self.create_window()
        self.window.mainloop()

    def create_window(self):
        window = tk.Tk()
        self.window = window
        window.title("NARS Vision Test")
        window.geometry("1400x650")

        self.HEIGHT, self.WIDTH = np.array(Image.open(dir_0 + "/" + os.listdir(dir_0)[0])).shape

        HEIGHT, WIDTH, ZOOM = self.HEIGHT, self.WIDTH, self.ZOOM

        # main image
        self.visual_image_canvas = tk.Canvas(window,
                                        width=WIDTH*ZOOM,
                                        height=HEIGHT*ZOOM,
                                        bg="#000000")
        self.visual_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                        height=HEIGHT * ZOOM)

        self.visual_image_canvas_img = self.visual_image_canvas.create_image((WIDTH*ZOOM / 2, HEIGHT*ZOOM / 2),
                                                                             image=self.visual_img,
                                                                             state="normal")

        # label
        self.status_label = tk.Label(window, text="Initializing...")


        # attended image
        self.attended_image_canvas = tk.Canvas(window,
                                             width=WIDTH * ZOOM,
                                             height=HEIGHT * ZOOM,
                                             bg="#000000")
        self.attended_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                          height=HEIGHT * ZOOM)
        self.attended_image_canvas_img = self.attended_image_canvas.create_image((WIDTH*ZOOM / 2, HEIGHT*ZOOM / 2),
                                                                               image=self.attended_img,
                                                                               state="normal")

        # sliders

        self.digit_to_label_lights = {}
        self.digit_to_label_sliders = {}
        self.digit_to_label_slider_guilabel = {}
        slider_row = 1
        column = 2

        for i in range(10):
            light = tk.Button(window,text="    ",bg="black")
            slider = tk.Scale(window, from_=1.0, to=0.0, digits = 3, resolution = 0.01)
            label = tk.Label(window, text=i)
            slider.set(0.5)
            light.grid(row=slider_row,column=column+2)
            slider.grid(row=slider_row+1, column=column, columnspan=3)
            label.grid(row=slider_row + 2, column=column+2)

            self.digit_to_label_lights[i] = light
            self.digit_to_label_sliders[i] = slider
            self.digit_to_label_slider_guilabel[i] = label
            column += 3

        self.button_correct = tk.Button(bg='grey', text="CORRECT")
        self.button_wrong = tk.Button(bg='grey', text="INCORRECT")

        self.visual_image_canvas.grid(row=0, column=1)
        self.attended_image_canvas.grid(row=0,column=2, columnspan=30)
        self.status_label.grid(row=1, column=1)


    def set_visual_image(self, new_img):
        self.visual_img = ImageTk.PhotoImage(new_img.resize((self.WIDTH * MNISTVisionTestGUI.ZOOM, self.HEIGHT * MNISTVisionTestGUI.ZOOM), Image.NEAREST))
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_attended_image_array(self, new_img_array):
        new_img = Image.fromarray(new_img_array)
        self.attended_img = ImageTk.PhotoImage(new_img.resize((new_img.width * MNISTVisionTestGUI.ZOOM, new_img.height * MNISTVisionTestGUI.ZOOM), Image.NEAREST))
        self.attended_image_canvas.itemconfig(self.attended_image_canvas_img, image=self.attended_img)

    def clear_visual_image(self):
        self.visual_img = tk.PhotoImage(width=self.WIDTH * MNISTVisionTestGUI.ZOOM, VisionTestGUI=self.HEIGHT * MNISTVisionTestGUI.ZOOM)
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_status_label(self, text):
        self.status_label.config(text=text)

    def update_sliders(self):
        # update last attended image
        self.set_attended_image_array(Global.Global.NARS.vision_buffer.last_taken_img_array)

        # update sliders
        for i in range(10):
            sentence = Global.Global.NARS.memory.peek_concept(digit_to_detected_term[i]).belief_table.peek()
            if sentence is not None:
                exp = sentence.get_expectation()
                self.digit_to_label_sliders[i].set(exp)

    def get_predicted_digit(self):
        operation_statement = Global.Global.NARS.last_executed
        predicted = -1
        if operation_statement is not None:
            for key in digit_to_goal_op_term:
                value = digit_to_goal_op_term[key]
                if value == operation_statement:
                    predicted = key

        # update GUI lights
        for i in range(10):
            if i == predicted:
                self.digit_to_label_lights[i].config(bg="white")
            else:
                self.digit_to_label_lights[i].config(bg="black")
        return predicted

    def get_predicted_bit(self):
        operation_statement = Global.Global.NARS.last_executed
        predicted = -1
        if operation_statement is not None:
            for key in digit_to_goal_op_term:
                value = digit_to_goal_op_term[key]
                if value == operation_statement:
                    predicted = key

        # update GUI lights
        for i in range(2):
            if i == predicted:
                self.digit_to_label_lights[i].config(bg="white")
            else:
                self.digit_to_label_lights[i].config(bg="black")
        return predicted



    def show_test_buttons(self):
        self.button_correct.grid(row=2, column=0)
        self.button_wrong.grid(row=3, column=0)


    def update_test_buttons(self, correct_digit, predicted_digit=-1):
        if correct_digit == -1:
            self.button_correct.config(bg='grey')
            self.button_wrong.config(bg='grey')
            return

        if correct_digit == predicted_digit:
            self.button_correct.config(bg='green')
            self.button_wrong.config(bg='grey')
        else:
            self.button_correct.config(bg='grey')
            self.button_wrong.config(bg='red')

def train(x_train, y_train, cycles):
    for train_idx,img_array in enumerate(x_train):
        img = Image.fromarray(img_array)
        InputChannel.queue_visual_sensory_image_array(img)
        global_gui.set_visual_image(img)

        label = digit_to_label[y_train[train_idx]]

        for i in range(cycles):
            Global.Global.NARS.do_working_cycle()
            InputChannel.parse_and_queue_input_string(label)

            global_gui.set_status_label('TRAINING:\nFile: #' + str(train_idx+1) + "/" + str(len(x_train)) + '\nCycle ' + str(i) + ' / ' + str(cycles) \
                                           + '\n' + str(round(i * 100 / cycles, 2)) + "%")
            global_gui.update_sliders()

def test(bit,
         x_test,
         y_test,
         cycles,
         break_duration):
    # seed goals
    seed_bit_goals() if bit else seed_digit_goals()

    # run tests
    global_gui.show_test_buttons()
    correct_cycles_cnt = 0
    incorrect_cycles_cnt = 0
    total_cycles_cnt = 0

    correct_examples_cnt = 0
    incorrect_examples_cnt = 0

    for test_idx,img_array in enumerate(x_test):
        img = Image.fromarray(img_array)
        InputChannel.queue_visual_sensory_image_array(img)
        global_gui.set_visual_image(img)

        break_time(break_duration)

        this_example_correct_cnt = 0
        this_example_incorrect_cnt = 0
        for i in range(cycles):
            Global.Global.NARS.do_working_cycle()
            global_gui.set_status_label('TESTING:\nFile: #' + str(test_idx+1) + "/" + str(len(x_test)) + '\nCycle ' + str(i) + ' / ' + str(cycles) \
                                           + '\n' + str(round(i * 100 / cycles, 2)) + "%")
            global_gui.update_sliders()

            prediction = global_gui.get_predicted_digit()

            if prediction != -1:
                global_gui.update_test_buttons(correct_digit=y_test[test_idx],
                                               predicted_digit=prediction)
                if prediction == y_test[test_idx]:
                    this_example_correct_cnt += 1
                else:
                    this_example_incorrect_cnt += 1

        if this_example_correct_cnt > this_example_incorrect_cnt:
            correct_examples_cnt += 1
        else:
            incorrect_examples_cnt += 1

        print('=========== Example Test Case Accuracy so far: ' + str(
            round(correct_examples_cnt / (test_idx+1) * 100, 2)) + "%")


    # print('======= CYCLE SUBTOTALS ========')
    # print('++ correct cycles:' + str(correct_cycles_cnt))
    # print('++ incorrect cycles:' + str(incorrect_cycles_cnt))
    # print('= TOTAL CYCLE Test Case Accuracy: ' + str(round(correct_cycles_cnt / (total_cycles_cnt) * 100, 2)) + "%")
    total_examples = correct_examples_cnt + incorrect_examples_cnt
    print('======= TEST EXAMPLE SUBTOTALS ========')
    print('++ correct examples:' + str(correct_examples_cnt))
    print('++ incorrect examples:' + str(incorrect_examples_cnt))
    print('=========== TOTAL EXAMPLE Test Case Accuracy: ' + str(round(correct_examples_cnt / total_examples * 100, 2)) + "%")


def test_main():
    Config.GUI_USE_INTERFACE = False
    Config.SILENT_MODE = True
    Global.Global.NARS = NARS.NARS()
    Global.Global.set_paused(False)

    #supervised_learning_0_or_1_one_example()
    supervised_learning_MNIST_0_or_1_dataset()
    #supervised_learning_MNIST()

global_gui = MNISTVisionTestGUI()
thread = threading.Thread(target=global_gui.start, daemon=True)
thread.start()

if __name__ == "__main__":
    test_main()