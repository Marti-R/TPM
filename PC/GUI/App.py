import datetime
import json
import multiprocessing as mp
import os
import sys
import time
import tkinter as tk
from multiprocessing import Process, Event
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from src.MyApp import create_setting_widgets, SettingsWindow, ListSettingsWindow
from src.MyApp import get_single_setting

trial_settings = {
    "repeats":{"value":5,"type":"int","randomizable":False,"label":"Number of trials"},
    "start_delay":{"value":0,"type":"float","randomizable":False,"label":"Start Delay"},
    "reward_delay":{"value":1,"type":"float","randomizable":False,"label":"Reward Delay"},
    "trial_timeout":{"value":1,"type":"float","randomizable":False,"label":"Trial Timeout"},
    "lick_timeout":{"value":1,"type":"float","randomizable":False,"label":"Lick Timeout"},
    "timeout_punish":{"value":1,"type":"float","randomizable":False,"label":"Timeout Punish"},
    "fail_punish":{"value":1,"type":"float","randomizable":False,"label":"Fail Punish Time"},
    "reward_time":{"value":1,"type":"float","randomizable":False,"label":"Reward Tim"},
}

bpod_settings = {

    "serial_port": {"value": "/dev/ttyACM0", "type": "file", "filetypes": [("Serial", "*ttyACM*")],"label":"Bpod Serial Port"},
    "session_name": {"value": "session", "randomizable": False, "type": "str","label":"Session Name"},

}

pi_settings = {

    "serial_port": {"value": "/dev/ttyACM0", "type": "file", "filetypes": [("Serial", "*ttyACM*")],"label":"Bpod Serial Port"},
    "session_name": {"value": "session", "randomizable": False, "type": "str","label":"Session Name"},

}

class Application(tk.Frame):

    def __init__(self,master = None):
        super().__init__(master)

        from tkinter import font
        f = font.nametofont(font.names()[7])

        self.bpod_process = None

        self.flags = {
            "pod_ready": Event(),
            "pi_ready": Event(),
            "run": Event()
        }

        self.trial_settings_template = trial_settings
        self.bpod_settings_template = bpod_settings
        self.pi_settings_template = pi_settings


        self.left_frame = tk.Frame(self.master)
        self.left_frame.pack(side = "left")

        self.right_frame = tk.Frame(self.master)
        self.right_frame.pack(side = "left")

        self.settings_frame = tk.Frame(self.left_frame)
        self.settings_frame.pack()

        tk.Label(self.settings_frame,text = "Experiment Settings", font=(f, 12, "bold")).pack()

        self.bpod_frame = tk.Frame(self.right_frame)
        self.bpod_frame.pack(side = "top")
        tk.Label(self.bpod_frame, text="Bpod Settings", font=(f, 12, "bold")).pack()

        self.pi_frame = tk.Frame(self.right_frame)
        self.pi_frame.pack(side = "top")
        tk.Label(self.pi_frame, text="Raspberrypi Settings", font=(f, 12, "bold")).pack()

        self.flag_frame = tk.Frame(self.right_frame)
        self.flag_frame.pack(side = "bottom")

        self.trial_controls = tk.Frame(self.left_frame)
        self.trial_controls.pack(side = "bottom")


        self.create_main_window()

        fig, ax = self.create_figure()

        self.fig = fig
        self.ax = ax

        self.chart = FigureCanvasTkAgg(self.fig, self.master)
        self.chart.get_tk_widget().pack()

    def create_figure(self):

        fig = plt.figure(constrained_layout=True, figsize=(10, 5))

        widths = [10,1]
        heights = [2,1,2]

        spec2 = mpl.gridspec.GridSpec(ncols=2, nrows=3, figure=fig, width_ratios=widths,
                                  height_ratios=heights)

        ax1 = fig.add_subplot(spec2[0, 0])
        ax2 = fig.add_subplot(spec2[:, 1])
        ax3 = fig.add_subplot(spec2[1, 0])
        ax4 = fig.add_subplot(spec2[2, 0])



        ax = {"session":ax1,"legend":ax2,"trace":ax3,"hist":ax4}
        return fig,ax

    def plot(self):
        from src.SessionPlotter import TPMSessionLoad, TPMSessionPlotter

        loader = TPMSessionLoad()
        loader.path = "./sessions/dummy_session.csv"
        loader.trial_indices = list(np.zeros(100, dtype=int))
        loader.trial_versions = [{"name": "standard"}]
        loader.load_session(loader.path)

        plotter = TPMSessionPlotter(loader)
        plotter.settings = {
            "ymin": 0,
            "ymax": 1,
            "hist_bins":10,
            "margin": 0.2,
            "state_bar_height": 0.05,
            "success_color": (0, 1, 0),
            "desaturation": 0.7,
            "fail_color": (1, 0, 0),
            "plot_window": 20,
            "workspace_path": "./experiments/",
            "figure_path": "./plot.pdf", "type": "df .png .jpg . svg",
        }

        loader.settings = plotter.settings
        plotter.plot_experiment(self.ax)
        plotter.plot_trace(self.ax["trace"])
        self.chart.draw()


    def create_main_window(self):
        self.make_trial_settings()
        self.make_bpod_settings()
        self.make_pi_settings()

        self.make_trial_controls()

        self.make_flag_widgets()

    def make_flag_widgets(self):
        pi_ready = tk.Label(self.flag_frame,text = "Pi Ready",bg = "red")
        pi_ready.pack()

        pod_read = tk.Label(self.flag_frame,text = "Bpod Ready",bg = "red")
        pod_read.pack()

        running = tk.Label(self.flag_frame,text = "Running",bg = "red")
        running.pack()

        self.flag_widgets = {
            "pi_ready":pi_ready,
            "pod_ready":pod_read,
            "run":running
        }

        self.update_flag_widgets()

    def update_flag_widgets(self):

        if self.flags["pi_ready"].is_set():
            self.flag_widgets["pi_ready"].configure(bg = "green")
        else:
            self.flag_widgets["pi_ready"].configure(bg="red")

        if self.flags["pod_ready"].is_set():
            self.flag_widgets["pod_ready"].configure(bg="green")
        else:
            self.flag_widgets["pod_ready"].configure(bg="red")

        if self.flags["run"].is_set():
            self.flag_widgets["run"].configure(bg = "green")
        else:
            self.flag_widgets["run"].configure(bg="red")

        self.after(100,self.update_flag_widgets)
    def make_trial_controls(self):

        self.send_settings_button = tk.Button(self.trial_controls,text="send settings", command = self.send_settings)
        self.send_settings_button.pack()

        self.initialize_button = tk.Button(self.trial_controls, text="Initialize", command=self.initialize)
        self.initialize_button.pack()

        self.start_button = tk.Button(self.trial_controls, text="Start Experiment", command=self.start_exp)
        self.start_button.pack()

        self.pause_button = tk.Button(self.trial_controls, text="Pause Experiment", command=self.pause_exp)
        self.pause_button.pack()

        self.plot_button = tk.Button(self.trial_controls, text="Plot", command=self.plot)
        self.plot_button.pack()

        self.quit_button = tk.Button(self.trial_controls, text="Quit Experiment", command=self.quit_exp)
        self.quit_button.pack()

    def make_trial_settings(self):

        def callback(export):
            pass

        self.trial_settings = SettingsWindow(self.settings_frame, self.trial_settings_template, callback, window = False)

    def make_bpod_settings(self):

        def callback(export):
            pass
        self.bpod_settings = SettingsWindow(self.bpod_frame, self.bpod_settings_template, callback,window = False)

    def make_pi_settings(self):

        def callback(export):
            pass

        self.pi_settings = SettingsWindow(self.pi_frame, self.pi_settings_template, callback, window = False)

        self.pi_ready_set_button = tk.Button(self.pi_frame, text="Pi ready", command=self.pi_ready_set)
        self.pi_ready_set_button.pack()

        self.pi_ready_clear_button = tk.Button(self.pi_frame, text="Pi not ready", command=self.pi_ready_clear)
        self.pi_ready_clear_button.pack()


    def pi_ready_set(self):

        self.flags["pi_ready"].set()

    def pi_ready_clear(self):

        self.flags["pi_ready"].clear()

    def get_settings(self):

        assert hasattr(self, "trial_settings")
        assert hasattr(self, "bpod_settings")
        assert hasattr(self, "pi_settings")

        trial = self.trial_settings.settings.get_experiment_variables().get_settings_dict()
        bpod = self.bpod_settings.settings.get_experiment_variables().get_settings_dict()
        pi = self.pi_settings.settings.get_experiment_variables().get_settings_dict()

        return trial, bpod, pi

    def send_settings(self):

        trial, bpod, pi = self.get_settings()


    def initialize(self):
        from src.tpm_bpod_script import run_single_trial, run_multiple_trials

        trial, bpod, pi = self.get_settings()

        self.flags["run"].clear()
        self.bpod_process = Process(target=run_multiple_trials, args=(trial,self.flags))
        self.bpod_process.start()


    def start_exp(self):

        if self.bpod_process is None or not self.bpod_process.is_alive():
            self.initialize()

        self.flags["run"].set()

    def pause_exp(self):

        self.flags["run"].clear()

    def quit_exp(self):

        if not self.bpod_process is None:
            self.bpod_process.terminate()

    def quit(self):

        self.quit_exp()
        self.master.destroy()
        self.master.quit()


root = tk.Tk()
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", root.quit)
app.mainloop()
sys.exit(0)
