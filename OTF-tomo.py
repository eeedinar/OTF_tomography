#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import tkinter as tk
import getpass
import subprocess
import re
import signal
import os
from tkinter import messagebox

#### Specifications
CWD          = os.getcwd()   # Raw_data will be created in this project directory
PYTHON_PATH  = '/programs/x86_64-linux/python/3.7.0/bin.capsules/python'
PROGRAMS_LOC = '/nfs/vast/emcenter/aalbashit/tomo/'

#Handles Ctrl-C within threads to exit program at least semi-gracefully - also stops relion background pipeline through RUNNING file
def ctrl_c_opt():
    print('\nWARNING: The pipeline has been stopped. All the current running pipelines, if any, quit now. \n\nWARNING: If you need to change the paramaters used in the initial command please remove all contents of directory prior to restarting\n')

    cmd = "ps -ef | grep .py | awk \'{ for (i = 2; i <= 2; ++i) printf $i\" \"}\'  | xargs kill -9"
    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    outs, errs = proc.communicate()  #     print(outs)    
    print(outs)
    root.quit()

def window_handler(event):
    print("You pressed Ctrl+C in program window")
    ctrl_c_opt()
def terminal_handler(event):
    print("You pressed Ctrl+C in terminal")
    ctrl_c_opt()
def check():
    root.after(500, check)  #  time in ms.
def float_test(gui_var, var_alias):
    try:
        float(gui_var.get())
        return ""
    except ValueError:
        return var_alias

class RelionItGui(object):

    def __init__(self, main_window):
        self.main_window = main_window

        class tkLine(object):

            def __init__(self, frame, vartype=None, inputtype=None, text="", options=[]):
                self.label = tk.Label(frame, text=text, bg=light_bg)
                if vartype == bool:
                    self.var = tk.BooleanVar()
                elif vartype == str:
                    self.var = tk.StringVar()
                if inputtype == "button":
                    self.input = tk.Checkbutton(frame, var=self.var)
                elif inputtype == "option":
                    self.input = tk.OptionMenu(frame, self.var, *options)
                elif inputtype == "entry":
                    self.input = tk.Entry(frame, textvariable=self.var, bg=entry_bg)

        def toggle(var, button):
            button.deselect() if var.get() else button.select()

        # Colour definitions
        entry_bg     = "#ffffe6"  # yellowish background for Entries
        button_bg    = "#c8506e"  # reddish colour for Browse buttons
        runbutton_bg = "#a01e3c"  # darker red for Run buttons
        grey_bg      = "#f3f3f3"  # grey frame background
        light_bg     = "white"    # white frame background

        ### Create GUI ###
        main_frame  = tk.Frame(main_window, bg=grey_bg)
        main_frame.pack(fill=tk.BOTH, expand=1)
        left_frame  = tk.Frame(main_frame, bg=grey_bg)
        left_frame.pack(side=tk.LEFT, anchor=tk.N, fill=tk.X, expand=1)
        right_frame = tk.Frame(main_frame, bg=grey_bg)
        right_frame.pack(side=tk.LEFT, anchor=tk.N, fill=tk.X, expand=1)

        # Frame padding
        padx = 15
        pady = 15

        ### PROJECT ###
        project_frame = tk.LabelFrame(left_frame, text="Project details", padx=padx, pady=pady, bg=light_bg)
        project_frame.pack(padx=padx, pady=pady, fill=tk.X, expand=1)
        tk.Grid.columnconfigure(project_frame, 1, weight=1)
        row = 0

        self.user = tkLine(project_frame, str, "entry", "Username:")
        self.user.label.grid(row=row, column=0, sticky=tk.W)
        self.user.input.grid(row=row, column=1, sticky=tk.W + tk.E)
        self.user.var.set(getpass.getuser())
        self.user.label.bind("<Button-1>", lambda event: self.user.input.focus_set())
        row += 1

        self.email = tkLine(project_frame, str, "entry", "Email:")
        self.email.label.grid(row=row, column=0, sticky=tk.W)
        self.email.input.grid(row=row, column=1, sticky=tk.W + tk.E)
        try:
            cmd = f"ipa user-find --login {getpass.getuser()}"
            run_output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            email = re.findall("Email address: (.+)", run_output.stdout)[0]
            self.email.var.set(email)
        except:
            pass
        self.email.label.bind("<Button-1>", lambda event: self.email.input.focus_set())
        row += 1

        self.runtime = tkLine(project_frame, str, "entry", "Runtime:")
        self.runtime.label.grid(row=row, column=0, sticky=tk.W)
        self.runtime.input.grid(row=row, column=1, sticky=tk.W)
        tk.Label(project_frame, text="(hr)").grid(row=row, column=1, sticky=tk.E)
        self.runtime.label.bind("<Button-1>", lambda event: self.runtime.input.focus_set())
        row += 1

        self.microscope = tkLine(project_frame, str, "option", "Microscope:", ["Krios1", "Krios2", "Talos"])
        self.microscope.label.grid(row=row, column=0, sticky=tk.W)
        self.microscope.input.grid(row=row, column=1, sticky=tk.W)
        self.microscope.input.configure(activebackground=light_bg, activeforeground="black", bg=light_bg)
        self.microscope.var.set("Krios1")
        row += 1   
        
        self.debug_ = tkLine(project_frame, bool, "button", "~~~ Debug?")
        self.debug_.label.grid(row=row, column=0, sticky=tk.W)
        self.debug_.input.grid(row=row, column=0, sticky=tk.W)
        self.debug_.label.bind("<Button-1>", lambda event: toggle(self.debug_.var, self.debug_.input))
        row += 1

        ### PREPROCESSING ###
        prep_frame = tk.LabelFrame(right_frame, text="Preprocessing settings", padx=padx, pady=pady, bg=light_bg)
        prep_frame.pack(padx=padx, pady=pady, fill=tk.X, expand=1)
        tk.Grid.columnconfigure(prep_frame, 1, weight=1)
        row = 0

        self.angpix = tkLine(prep_frame, str, "entry", "Pixel size:")
        self.angpix.label.grid(row=row, column=0, sticky=tk.W)
        self.angpix.input.grid(row=row, column=1, sticky=tk.W)
        tk.Label(prep_frame, text="(A\u00B2)").grid(row=row, column=2, sticky=tk.E)
        self.angpix.label.bind("<Button-1>", lambda event: self.angpix.input.focus_set())
        row += 1

        self.exposure = tkLine(prep_frame, str, "entry", "Exposure rate:")
        self.exposure.label.grid(row=row, column=0, sticky=tk.W)
        self.exposure.input.grid(row=row, column=1, sticky=tk.W)
        tk.Label(prep_frame, text="(e-/A\u00B2/frame)").grid(row=row, column=2, sticky=tk.W)
        self.exposure.label.bind("<Button-1>", lambda event: self.exposure.input.focus_set())
        row += 1

        self.superres = tkLine(prep_frame, bool, "button", "~~~ Super-resolution?")
        self.superres.label.grid(row=row, column=0, sticky=tk.W)
        self.superres.input.grid(row=row, column=0, sticky=tk.W)
        self.superres.label.bind("<Button-1>", lambda event: toggle(self.superres.var, self.superres.input))
        row += 1
        
        button_frame = tk.Frame([left_frame, right_frame][1], bg=grey_bg)
        button_frame.pack(padx=padx, pady=0, fill=tk.X, expand=1)
        self.run_button = tk.Button(button_frame,
                                    text="Run Pipeline",
                                    command=self.run_pipeline,
                                    activebackground=button_bg,
                                    activeforeground="white",
                                    bg=runbutton_bg,
                                    fg="white")
        self.run_button.pack(padx=0, pady=0, side=tk.TOP, fill=tk.BOTH, expand=1)

    ### RUN PIPELINE BUTTON ###
    def run_pipeline(self):
        warn = [float_test(self.angpix.var, "Pixel size"), float_test(self.runtime.var, "Runtime"), float_test(self.exposure.input, "Exposure rate")]
        warn_str = " ".join(warn).strip()  # 'Pixel size Runtime Exposure rate'
        if len(warn_str):
            messagebox.showwarning("Error:",  ", ".join([i  for i in warn if len(i)]) + " must be a number.")
            return

        self.main_window.destroy()
        # path where data to come from
        SOURCE_PATH = f'/cifs/{self.microscope.var.get()}/{self.user.var.get()}/DATA/'
        cmd = [PYTHON_PATH, os.path.join(PROGRAMS_LOC, 'backend_master.py'), '--username', self.user.var.get(), '--microscope', \
            self.microscope.var.get() ,'--runtime', self.runtime.var.get(), '--pixel_size', self.angpix.var.get(),\
                '--working_dir', CWD, '--python_path', PYTHON_PATH, '--prog_loc', PROGRAMS_LOC, '--exposure_rate', self.exposure.var.get() ,\
                    '--source_dir', SOURCE_PATH,'--debug', str(self.debug_.var.get()), '--super_res', str(self.superres.var.get()) ]

        if bool(self.email.var.get().strip()):
            cmd += ['--email', self.email.var.get()]
        if bool(self.exposure.var.get().strip()):
            cmd += ['--exposure_rate', self.exposure.var.get()] 

        subprocess.run(cmd)

        return

root = tk.Tk()
root.title("OTF-tomo")
gui = RelionItGui(root)
signal.signal(signal.SIGINT, lambda x,y : print('terminal ^C') or terminal_handler(None))
root.after(500, check)  #  time in ms.  # "context switch" that allows the ^C to be caught by the signal_handler. - 
root.bind_all('<Control-c>', window_handler)  # windows control C to operate function
root.mainloop()
