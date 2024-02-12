import gc
import glob
import queue
import random
import threading
import time

import numpy as np
from keras.datasets import mnist, cifar10

import Config
import Global
import InputChannel
import NARS
import NALGrammar

from PIL import Image, ImageTk
import os
import tkinter as tk

from NALGrammar.Sentences import Judgment
from NARSMemory import Concept


class GenericVisionTest:
    def __init__(self,
                 dataset_loader,
                 gui_enabled,
                 train_size,
                 test_size,
                 training_cycles):
        self.current_trial = 0
        (self.x_train, self.y_train), (self.x_test, self.y_test) = dataset_loader.load_data()

        self.break_duration = 20

        # shuffle dataset
        p = np.random.permutation(len(self.x_train))
        self.x_train, self.y_train = self.x_train[p], self.y_train[p]
        p = np.random.permutation(len(self.x_test))
        self.x_test, self.y_test = self.x_test[p], self.y_test[p]

        # trim dataset to size
        self.x_train, self.y_train = self.x_train[0:train_size], self.y_train[0:train_size]
        self.x_test, self.y_test = self.x_train[0:test_size], self.y_train[0:test_size]

        # reshape data
        self.y_train = np.reshape(self.y_train, newshape=(self.y_train.shape[0]))
        self.y_test = np.reshape(self.y_test, newshape=(self.y_test.shape[0]))

        # concat data
        self.y_total = np.concatenate((self.y_train, self.y_test))

        # store labels and NARS objects
        self.numeric_labels = np.unique(self.y_total)
        self.numeric_label_to_term_string = {}
        self.numeric_label_to_term = {}
        for label in self.numeric_labels:
            term_str = self.get_label_Narsese_statement_string(label)
            self.numeric_label_to_term_string[label] = term_str + ". :|: %1.0;0.99%"
            self.numeric_label_to_term[label] = NALGrammar.Terms.from_string(term_str)

        self.global_gui = VisionTestGUI(28,
                                        self.numeric_labels,
                                        self.numeric_label_to_term,
                                        gui_enabled,
                                        dataset_loader=dataset_loader)
        self.training_cycles = training_cycles
        self.TIMEOUT = 500  # in working cycles

    def run_main_test(self):
        if self.global_gui.gui_disabled:
            self.global_gui.start()
        else:
            thread = threading.Thread(target=self.global_gui.start, daemon=True)
            thread.start()

        time.sleep(1)

        learn_parameters = False
        if learn_parameters:
            self.learn_best_params()
        else:
            self.run_test()

        time.sleep(10)

    def load_dataset(self):
        return self.x_train, self.y_train, self.x_test, self.y_test

    @classmethod
    def restart_NARS(cls):
        Config.GUI_USE_INTERFACE = False
        Config.SILENT_MODE = True
        if Global.Global.NARS is not None: del Global.Global.NARS
        Global.Global.NARS = NARS.NARS()
        Global.Global.set_paused(False)
        gc.collect()

    def train(self):
        print('Begin Training Phase')
        self.global_gui.toggle_test_buttons(on=False)
        for train_idx, img_array in enumerate(self.x_train):
            img = Image.fromarray(img_array)
            InputChannel.queue_visual_sensory_image_array(img)
            self.global_gui.set_visual_image(img)

            label = self.numeric_label_to_term_string[self.y_train[train_idx]]
            print('TRAINING label ' + str(self.y_train[train_idx]) \
                  + ':\nFile: #' + str(train_idx + 1) + "/" + str(len(self.x_train)) + ' for ' + str(
                self.training_cycles) + ' cycles')

            for i in range(self.training_cycles):
                Global.Global.NARS.do_working_cycle()
                InputChannel.parse_and_queue_input_string(label)
                self.global_gui.set_status_label(
                    'TRAINING:\nFile: #' + str(train_idx + 1) + "/" + str(len(self.x_train))
                    + '\nCycle ' + str(i) + ' / ' + str(self.training_cycles) \
                    + '\n' + str(round(i * 100 / self.training_cycles, 2)) + "%")
                self.global_gui.update_spotlight()

    def test(self):

        print('Begin Testing Phase')
        # run tests
        self.global_gui.toggle_test_buttons(on=True)

        # examples accuracy measurements
        correct_examples_total_cnt = 0
        incorrect_examples_total_cnt = 0
        correct_cnt_dict = {}
        incorrect_cnt_dict = {}

        for i in self.numeric_labels:
            correct_cnt_dict[i] = 0
            incorrect_cnt_dict[i] = 0

        for test_idx, img_array in enumerate(self.x_test):
            label_y = self.y_test[test_idx]
            img = Image.fromarray(img_array)
            InputChannel.queue_visual_sensory_image_array(img)
            self.global_gui.set_visual_image(img)
            self.global_gui.update_test_actual_label(label=str(label_y) + " (" + self.global_gui.class_number_to_string_label(label_y) + ")")

            # blank out GUI lights
            self.global_gui.update_gui_lights(predicted=-1, label_y=None)
            self.break_time(self.break_duration)

            print('TESTING next example, class ' + str(label_y) + ':\nFile: #'
                  + str(test_idx + 1) + "/" + str(len(self.x_test)))

            # let NARS think and come to a prediction
            prediction = -1
            i = 0
            while prediction == -1 and i < self.TIMEOUT:  #
                Global.Global.NARS.do_working_cycle()
                self.global_gui.set_status_label('TESTING:\nFile: #'
                                                 + str(test_idx + 1) + "/" + str(len(self.x_test)) + '\nCycle ' + str(
                    i))
                self.global_gui.update_spotlight()
                self.global_gui.update_gui_sliders()

                prediction = self.global_gui.get_predicted_label()
                self.seed_goals()
                i += 1

            # check prediction
            correct = None
            if prediction == label_y:
                correct_examples_total_cnt += 1
                correct_cnt_dict[label_y] += 1
                correct = True
            else:
                incorrect_examples_total_cnt += 1
                incorrect_cnt_dict[label_y] += 1
                correct = False
            self.global_gui.update_test_buttons(correct=correct)
            self.global_gui.update_gui_lights(prediction, label_y)

            accuracy = round(correct_examples_total_cnt / (test_idx + 1) * 100, 2)
            print("=========== System predicted " + str(prediction) + " and actual was " + str(label_y))
            print('=========== Trial Accuracy so far: ' + str(accuracy) + "%")

            self.global_gui.update_test_accuracy(accuracy=accuracy, current_trial=self.current_trial)

            if test_idx >= 9 and accuracy < 0.001:
                print("Aborting trial, parameters could not identify anything in 10 tests.")
                break

        total_examples = len(self.x_test)
        total_accuracy = round(correct_examples_total_cnt / total_examples * 100, 2)

        print('======= Test Subtotals ========')
        for i in self.numeric_labels:
            print('+!+ Class ' + str(i) + ' examples (correct | incorrect | total):' \
                  + str(correct_cnt_dict[i]) \
                  + " | " + str(incorrect_cnt_dict[i])
                  + " | " + str(correct_cnt_dict[i] + incorrect_cnt_dict[i]))
        print('+!+ OVERALL TOTAL examples (correct | incorrect | total):' \
              + str(correct_examples_total_cnt) \
              + " | " + str(incorrect_examples_total_cnt)
              + " | " + str(correct_examples_total_cnt + incorrect_examples_total_cnt))
        print('=!=========!= OVERALL TOTAL Test Accuracy: ' + str(total_accuracy) + "%")

        # fitness function
        return total_accuracy

    def learn_best_params(self):
        # current_params = {'PROJECTION_DECAY_DESIRE': Config.PROJECTION_DECAY_DESIRE,
        #                   'PROJECTION_DECAY_EVENT': Config.PROJECTION_DECAY_EVENT,
        current_params = {'T': Config.T,
                          'k': Config.k}

        best_params = current_params.copy()

        runs = 10000
        current_best_score = 0
        for i in range(runs):
            restart_NARS()

            # then use the better config.
            if i != 0:
                # mutate current params
                num_to_mutate = random.randint(1, len(current_params))
            else:
                num_to_mutate = 0

            current_params_list = list(current_params)
            for j in range(num_to_mutate):
                index = random.randint(0, len(current_params_list) - 1)
                key = current_params_list[index]
                new_param = current_params[key]

                # with a random sign increment
                sign = random.randint(0, 1)

                if key == 'k':
                    inc = random.random()
                    if sign == 0 and new_param - inc >= 1:
                        # 0 will be negative
                        new_param += -1 * inc
                    else:
                        # 1 will be positive
                        new_param += inc
                else:
                    inc = random.random()
                    if sign == 0:
                        # 0 will be negative
                        new_param += -1 * inc * new_param
                    else:
                        # 1 will be positive
                        new_param += inc * (1 - new_param)

                if key == 'T' and new_param < 0.55: new_param = 0.55

                if new_param < 0.00001: new_param = 0.00001

                current_params[key] = new_param

            # set NARS Params
            # Config.PROJECTION_DECAY_DESIRE = current_params['PROJECTION_DECAY_DESIRE']
            # Config.PROJECTION_DECAY_EVENT = current_params['PROJECTION_DECAY_EVENT']
            Config.T = current_params['T']
            Config.FOCUSX = current_params['FOCUSX']
            Config.FOCUSY = current_params['FOCUSY']
            Config.k = current_params['k']

            print('--TRYING NEW PARAMS--')
            for key in current_params:
                print('trying new ' + str(key) + ': ' + str(current_params[key]))

            q = queue.Queue()
            t = threading.Thread(target=run_trials, args=[q, 0], daemon=True)
            t.start()
            t.join()
            avg_result = q.get(block=True)

            if avg_result is None:
                print(
                    "!!! Score for these parameters could not keep up with the current best. Skipping them and Reverting Configs to best...")
                current_params = best_params.copy()
            else:
                print('Config optimization result ratio was: ' + str(avg_result))
                if avg_result > current_best_score:
                    # store new best params and score
                    print(']]]]]]]]]]]]]]]]] NEW BEST: ' + str(avg_result) +
                          ' beating ' + str(current_best_score) + ' [[[[[[[[[[[[[[[[')
                    current_best_score = avg_result
                    best_params = current_params.copy()
                elif avg_result == current_best_score:
                    # store new best params and score
                    print(']]]]]]]]]]]]]]]]] TIE: ' + str(avg_result) +
                          ' === ' + str(current_best_score) + ' [[[[[[[[[[[[[[[[')
                    best_params = current_params.copy()
                else:
                    print('WORSE result. Reverting Configs to best...')
                    current_params = best_params.copy()

            # print current best params
            print('--CURRENT BEST ' + str(current_best_score) + ' --')
            for key in best_params:
                print('BEST ' + str(key) + ': ' + str(best_params[key]))

        print('[][][][][][][][][][][][] OVERALL BEST CONFIG RESULTS (ratio ' + str(current_best_score) + '):')
        for key in best_params:
            print('BEST ' + str(key) + ': ' + str(best_params[key]))

    def run_trials(self, q, current_best_score, function):
        sum_of_scores = 0
        trials = 3

        for trial in range(trials):
            print("===== STARTING TRIAL " + str(trial + 1) + " / " + str(trials))

            self.current_trial = trial
            score = function()

            print("===== TRIAL " + str(trial + 1) + " ACCURACY: " + str(score) + "%")
            sum_of_scores += score

            if current_best_score is not None and trial != trials - 1:
                theoretical_best = sum_of_scores
                for _ in range(trial + 1, trials):
                    theoretical_best += 100  # plus the maximum score for the rest of the trials

                theoretical_best = theoretical_best / trials

                if theoretical_best < current_best_score:
                    # if the system can theoretically be perfect in the next trials and still have a worse average
                    # accuracy than the current best, just skip this configuration altogether
                    return None

        avg_score = round(sum_of_scores / trials, 2)
        q.put(avg_score)

    def run_test(self):
        q = queue.Queue()
        t = threading.Thread(target=self.run_trials, args=[q, 0, self.classification], daemon=True)
        t.start()
        t.join()

        self.global_gui.create_final_score_popup_window(final_score=q.get(block=True))

    def break_time(self, duration, clear_img=False):
        print('BREAK TIME...')
        # give the system a small break
        self.global_gui.update_test_buttons(None)
        if clear_img:
            Global.Global.NARS.vision_buffer.blank_image()
            self.global_gui.clear_visual_image()
            self.global_gui.set_visual_image(Image.fromarray(Global.Global.NARS.vision_buffer.img))
        self.global_gui.set_status_label('BREAK TIME...')
        for i in range(duration):
            Global.Global.NARS.do_working_cycle()
            self.global_gui.set_status_label('BREAK:\ncycle ' + str(i) + ' / ' + str(duration) \
                                             + '\n' + str(round(i * 100 / duration, 2)) + "%")
            self.global_gui.update_spotlight()
            self.global_gui.update_gui_sliders()

        print('END BREAK...')

    def seed_goals(self):
        """
        Seed goals to identify digit
        :return:
        """
        for i in self.numeric_labels:
            label = ("(&/," + self.get_label_Narsese_statement_string(i)
                     + ","
                     + self.get_seed_goal_statement_string(i) + ")"
                     + "! :|: %1.0;0.99%")
            InputChannel.parse_and_queue_input_string(label)

    @classmethod
    def get_label_Narsese_statement_string(cls, i):
        return "(" + str(i) + " --> SEEN)"

    def memorization(self): \
            assert False, "todo"

    # self.restart_NARS()
    #
    # x = np.concatenate((self.x_train, self.x_test), axis=0)
    # y = np.concatenate((self.y_train, self.y_test), axis=0)
    #
    # """
    #     Training Phase
    # """
    # self.train()
    #
    # """
    #     Testing Phase
    # """
    # return self.test()

    def classification(self):
        self.restart_NARS()

        """
            Training Phase
        """
        self.train()

        """
            Testing Phase
        """
        return self.test()

    @classmethod
    def get_seed_goal_statement_string(cls, label):
        return "((*,{SELF}) --> press_label_" + str(label) + ")"


class VisionTestGUI:
    ZOOM = 16
    gui_disabled = False

    def __init__(self,
                 size,
                 numeric_labels,
                 numeric_label_to_term,
                 gui_enabled,
                 dataset_loader):
        self.numeric_label_to_term = numeric_label_to_term
        self.HEIGHT, self.WIDTH = size, size
        self.numeric_labels = numeric_labels
        self.numeric_label_to_term = numeric_label_to_term
        self.gui_disabled = not gui_enabled
        self.dataset_loader = dataset_loader

        self.label_to_goal_op_term = {}
        for i in self.numeric_labels:
            term_str = GenericVisionTest.get_seed_goal_statement_string(label=i)
            term = NALGrammar.Terms.from_string(term_str)
            self.label_to_goal_op_term[i] = term

    def start(self):
        if self.gui_disabled: return
        self.create_window()
        self.window.mainloop()

    def create_window(self):
        if self.gui_disabled: return
        window = tk.Tk()
        self.window = window
        window.title("NARS Vision Test")
        window.geometry("1000x650")

        HEIGHT, WIDTH, ZOOM = self.HEIGHT, self.WIDTH, self.ZOOM

        # main image
        self.visual_image_canvas = tk.Canvas(window,
                                             width=WIDTH * ZOOM,
                                             height=HEIGHT * ZOOM,
                                             bg="#000000")
        self.visual_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                        height=HEIGHT * ZOOM)

        self.visual_image_canvas_img = self.visual_image_canvas.create_image((WIDTH * ZOOM / 2, HEIGHT * ZOOM / 2),
                                                                             image=self.visual_img,
                                                                             state="normal")

        # label
        self.status_label = tk.Label(window, text="Initializing...")
        self.test_accuracy_label = tk.Label(window, text="Test Accuracy: Need more data")
        self.test_actual_label = tk.Label(window, text="Actual Label: ")

        # attended image
        self.attended_image_canvas = tk.Canvas(window,
                                               width=WIDTH * ZOOM,
                                               height=HEIGHT * ZOOM,
                                               bg="#000000")
        self.attended_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                          height=HEIGHT * ZOOM)
        self.attended_image_canvas_img = self.attended_image_canvas.create_image((WIDTH * ZOOM / 2, HEIGHT * ZOOM / 2),
                                                                                 image=self.attended_img,
                                                                                 state="normal")

        # sliders
        self.numeric_label_to_term_string = {}
        self.numeric_label_to_term_string_lights = {}
        self.numeric_label_to_term_string_sliders = {}
        column = 2

        self.NARS_guess_label = tk.Label(window, text="NARS Guess:")

        for i in self.numeric_labels:
            light = tk.Button(window, text="    ", bg="black")
            label = tk.Label(window, text=self.class_number_to_string_label(i))
            slider = tk.Scale(window, from_=1.0, to=0.0, resolution=0.01)
            self.numeric_label_to_term_string_lights[i] = light
            self.numeric_label_to_term_string[i] = label
            self.numeric_label_to_term_string_sliders[i] = slider
            column += 3

        self.button_correct = tk.Button(bg='grey', text="CORRECT")
        self.button_wrong = tk.Button(bg='grey', text="INCORRECT")

        self.visual_image_canvas.grid(row=0, column=1)
        self.attended_image_canvas.grid(row=0, column=2, columnspan=30)
        self.status_label.grid(row=1, column=1)

    def set_visual_image(self, new_img):
        if self.gui_disabled: return
        self.visual_img = ImageTk.PhotoImage(
            new_img.resize((self.WIDTH * self.ZOOM, self.HEIGHT * self.ZOOM), Image.NEAREST))
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_attended_image_array(self, img_array):
        if self.gui_disabled: return
        new_img = Image.fromarray(img_array)
        self.attended_img = ImageTk.PhotoImage(
            new_img.resize((new_img.width * self.ZOOM, new_img.height * self.ZOOM), Image.NEAREST))
        self.attended_image_canvas.itemconfig(self.attended_image_canvas_img, image=self.attended_img)

    def clear_visual_image(self):
        if self.gui_disabled: return
        self.visual_img = tk.PhotoImage(width=self.WIDTH * self.ZOOM, height=self.HEIGHT * self.ZOOM)
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_status_label(self, text):
        if self.gui_disabled: return
        self.status_label.config(text=text)

    def update_spotlight(self):
        if self.gui_disabled: return
        # update last attended image
        if Global.Global.NARS.vision_buffer.last_taken_img_array is not None:
            self.set_attended_image_array(Global.Global.NARS.vision_buffer.last_taken_img_array)

    def get_predicted_label(self):
        operation_statement = Global.Global.NARS.last_executed
        predicted = -1
        if operation_statement is not None:
            for key in self.label_to_goal_op_term:
                value = self.label_to_goal_op_term[key]
                if value == operation_statement:
                    predicted = key

        return predicted

    def update_gui_lights(self, predicted, label_y):
        if self.gui_disabled: return
        # update GUI lights
        for i in self.numeric_labels:
            if i == predicted:
                if predicted == label_y:
                    self.numeric_label_to_term_string_lights[i].config(bg="green")
                else:
                    self.numeric_label_to_term_string_lights[i].config(bg="red")
            else:
                self.numeric_label_to_term_string_lights[i].config(bg="black")

        time.sleep(1.0)
        return predicted

    def update_gui_sliders(self):
        for classnum in self.numeric_labels:
            class_label_concept: Concept = Global.Global.NARS.memory.peek_concept(self.numeric_label_to_term[classnum])
            belief: Judgment = class_label_concept.belief_table.peek()
            if belief is None:
                self.update_gui_slider(classnum, 0.5)
            else:
                self.update_gui_slider(classnum, belief.get_expectation())

    def update_gui_slider(self, i, value):
        self.numeric_label_to_term_string_sliders[i].set(value=value)

    def toggle_test_buttons(self, on):
        if self.gui_disabled: return

        if on:
            self.button_correct.grid(row=2, column=0)
            self.button_wrong.grid(row=3, column=0)
            self.test_accuracy_label.grid(row=2, column=1)
            self.test_actual_label.grid(row=3, column=1)

            column = 4
            self.NARS_guess_label.grid(row=1, column=column, columnspan=30)
            for i in self.numeric_labels:
                self.numeric_label_to_term_string_lights[i].grid(row=2, column=column)
                self.numeric_label_to_term_string[i].grid(row=3, column=column)
                self.numeric_label_to_term_string_sliders[i].grid(row=4, column=column)
                column += 3
        else:
            self.update_test_buttons(correct=None)
            self.button_correct.grid_remove()
            self.button_wrong.grid_remove()
            self.test_accuracy_label.grid_remove()
            self.test_actual_label.grid_remove()

            column = 4
            self.NARS_guess_label.grid_remove()
            for i in self.numeric_labels:
                self.numeric_label_to_term_string_lights[i].grid_remove()
                self.numeric_label_to_term_string[i].grid_remove()
                self.numeric_label_to_term_string_sliders[i].grid_remove()
                column += 3

    def update_test_buttons(self, correct):
        if self.gui_disabled: return

        if correct is not None:
            if correct:
                self.button_correct.config(bg='green')
                self.button_wrong.config(bg='grey')
            else:
                self.button_correct.config(bg='grey')
                self.button_wrong.config(bg='red')
        else:
            self.button_correct.config(bg='grey')
            self.button_wrong.config(bg='grey')

    def update_test_accuracy(self, accuracy: float, current_trial: int):
        if self.gui_disabled: return
        self.test_accuracy_label.config(text="TRIAL " + str(current_trial + 1) + " ACCURACY: " + str(accuracy) + "%")

    def update_test_actual_label(self, label: str):
        if self.gui_disabled: return
        self.test_actual_label.config(text="Actual Label: " + label)

    def create_final_score_popup_window(self, final_score: float):
        if self.gui_disabled: return
        popup_window = tk.Toplevel(self.window)
        labelExample = tk.Label(popup_window,
                                text="AVERAGE TEST CASE\nACCURACY OVER 3 TRIALS:\n\n" + str(final_score) + "%\n\n")
        buttonExample = tk.Button(popup_window, text="OK", command=popup_window.destroy)

        labelExample.pack()
        buttonExample.pack()

    def class_number_to_string_label(self, i):
        if self.dataset_loader == mnist:
            return str(i)
        elif self.dataset_loader == cifar10:
            if i == 0:
                return "airplane"
            elif i == 1:
                return "automobile"
            elif i == 2:
                return "bird"
            elif i == 3:
                return "cat"
            elif i == 4:
                return "deer"
            elif i == 5:
                return "dog"
            elif i == 6:
                return "frog"
            elif i == 7:
                return "horse"
            elif i == 8:
                return "ship"
            elif i == 9:
                return "truck"


