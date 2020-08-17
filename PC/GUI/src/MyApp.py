import tkinter as tk
from copy import copy

from .MyVariables import MySettingGroup, MySetting, MyTrialSettings


class SettingsWindow:

    def __init__(self, root, settings_template, callback, window = True):


        self.callback = callback
        self.settings_template = settings_template

        if window:
            self.frame = tk.Toplevel(root)
            self.button_frame = tk.Frame(self.frame)
            self.button_frame.pack(side="bottom")
        else:
            self.frame = tk.Frame(root)
            self.frame.pack()
            self.button_frame = tk.Frame(self.frame)


        self.settings_frame = tk.Frame(self.frame)
        self.settings_frame.pack(side="top")


        self.settings = create_setting_widgets(settings_template)

        if isinstance(self.settings_template,dict):
            self.settings.create_widgets(self.settings_frame)


        elif isinstance(self.settings_template,list):
            for s in self.settings:
                s.create_widgets(self.settings_frame)


        exit_button = tk.Button(self.button_frame, text="Exit", command=self.close)
        exit_button.pack(side="right")

        apply_button = tk.Button(self.button_frame, text="Apply", command=self.apply)
        apply_button.pack(side="right")

        save_button = tk.Button(self.button_frame, text="Save", command=self.save)
        save_button.pack(side="right")


    def close(self):

        self.frame.destroy()

    def save(self):
        if self.apply():
            self.close()

    def apply(self):

        if isinstance(self.settings_template,dict):
            # self.settings.make_values()
            export = self.settings.export_settings()
            if not export:
                return False

        elif isinstance(self.settings_template,list):
            export = []
            for s in self.settings:
                s.make_values()

                export.append(s.export_settings())

        if None in export:
            return False

        self.callback(export)
        return True

class ListSettingsWindow(SettingsWindow):

    def __init__(self, root, settings_template, callback):


        self.callback = callback
        self.settings_template = settings_template

        self.frame = tk.Toplevel(root)
        self.top_frame = tk.Frame(self.frame)
        self.top_frame.pack(side = "top")

        self.settings_frame = tk.Frame(self.top_frame)
        self.settings_frame.pack(side="right")

        self.listbox_frame = tk.Frame(self.top_frame)
        self.listbox_frame.pack(side = "left",fill = "y",expand = True)

        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(side="bottom")


        self.settings = create_setting_widgets(settings_template)

        for i in self.settings:
            i.create_widgets(self.settings_frame,pack=False)

        setting_names = [i.get_experiment_variables().get_variable("name") for i in self.settings]

        self.listbox = tk.Listbox(self.listbox_frame)
        for name in setting_names:
            self.listbox.insert(tk.END,name)
        self.listbox.bind("<<ListboxSelect>>", self.update_selection)
        self.listbox.pack(fill = "y",expand = True)

        self.settings[0].show_widgets()

        exit_button = tk.Button(self.button_frame, text="Exit", command=self.close)
        exit_button.pack(side="right")

        apply_button = tk.Button(self.button_frame, text="Apply", command=self.apply)
        apply_button.pack(side="right")

        save_button = tk.Button(self.button_frame, text="Save", command=self.save)
        save_button.pack(side="right")

    def update_selection(self,event):

        sel = self.listbox.curselection()
        i = 0 if len(sel)  == 0 else sel[0]

        for setting in self.settings:
            setting.hide_widgets()

        self.settings[i].show_widgets()


    def close(self):

        self.frame.destroy()


    def apply(self):

        export = []
        for s in self.settings:
            s.make_values()
            export.append(s.export_settings())

        self.callback(export)

def get_simple_setting(k, v):
    return MySetting(k, v)


def get_dict_setting( k, v):
    if len(v.values()) == 1:
        v = list(v.items())[0]
        setting = get_simple_setting(v[0], v[1])

    else:
        value = v["value"] if "value" in v else 0

        setting = MySetting(k, value, **v)
        setting.randomizable = v["randomizable"] if "randomizable" in v else False
        t = v["type"]
        if t == "int":
            setting.type = int
        elif t == "float":
            setting.type = float
        elif t == "bool":
            setting.type = bool
        elif t == "str":
            setting.type = str
        elif t == "file" or t == "saveas":
            setting.type  = t
            if "filetypes" in v:
                setting.filetypes = v["filetypes"]
        elif t == "color":
            setting.type = "color"
        else:
            raise Exception

    return setting


def get_group_setting(k, v):
    setting_group = MySettingGroup(k, group_settings=v[0])

    for s in v[1:]:
        name = list(s.keys())[0]
        value = list(s.values())[0]
        setting = get_single_setting(name, value).settings[0]

        setting_group.append_setting(setting)

    return setting_group


def get_single_setting(k, v):
    setting_group = MySettingGroup(k)

    if isinstance(v, dict):

        setting = get_dict_setting(k, v)
        setting_group.append_setting(setting)

    else:
        setting = get_simple_setting(k, v)
        setting_group.append_setting(setting)

    return setting_group


def create_setting_widgets(settings_dict):
    """input may be a list"""

    if isinstance(settings_dict,dict):
        return create_single_settings_widget(settings_dict)

    elif isinstance(settings_dict,list):
        result = []
        for d in settings_dict:
            result.append(create_single_settings_widget(d))
        return result



def create_single_settings_widget(settings_dict):
    trail_settings = MyTrialSettings()

    for k, v in settings_dict.items():

        if isinstance(v, list):
            setting_group = get_group_setting(k, v)
            trail_settings.append_group(setting_group)

        else:

            trail_settings.append_group(get_single_setting(k, v))

    return trail_settings