import os
import shutil
import json
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from queue import Queue, Empty


#############################
# Configuration
#############################

SOURCE_FOLDER = "./core"  # For cloning
PLATFORMS = ["win32", "linux", "macos"]
ARCHS = ["x64", "arm64", 'ia32', 'arm7l']

#############################
# Main GUI Class
#############################

class BitmatoHyperfyGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bitmato - Hyperfy Electron Client")
        self.geometry("600x600")
        self.configure(bg="#1e1e2d")

        # ========== Mode selection ==========
        self.mode_var = tk.StringVar(value="Clone")

        # ========== Clone variables ==========
        self.project_name_var = tk.StringVar(value="MyElectronApp")
        self.remote_url_var = tk.StringVar(value="https://hyperfy.bitmato.dev")
        self.window_width_var = tk.StringVar(value="1024")
        self.window_height_var = tk.StringVar(value="768")
        self.cache_expiration_var = tk.StringVar(value="24")
        self.is_dev_var = tk.BooleanVar(value=False)
        self.start_max_var = tk.BooleanVar(value=False)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.tray_enabled_var = tk.BooleanVar(value=False)
        self.disable_cache_var = tk.BooleanVar(value=False)
        self.hw_accel_var = tk.BooleanVar(value=True)
        self.custom_user_agent_var = tk.StringVar(value="")

        # ========== Build variables ==========
        self.build_project_folder_var = tk.StringVar(value=os.getcwd())
        self.build_platform_var = tk.StringVar(value="win32")
        self.build_arch_var = tk.StringVar(value="x64")

        # Spinner references
        self.progress_window = None
        self.progress_label = None
        self.progress_bar = None
        
        self.output_queue = Queue()

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self, text="Bitmato - Hyperfy Electron Client",
            font=("Arial", 16, "bold"), fg="white", bg="#1e1e2d"
        )
        title_label.pack(pady=10)

        # Notebook for two tabs
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(pady=5, padx=5, fill="both", expand=True)

        # Clone tab
        self.clone_frame = tk.Frame(self.main_notebook, bg="#1e1e2d")
        self.main_notebook.add(self.clone_frame, text="Clone Project")
        self.build_clone_ui()

        # Build tab
        self.build_frame = tk.Frame(self.main_notebook, bg="#1e1e2d")
        self.main_notebook.add(self.build_frame, text="Build Project")
        self.build_build_ui()

        # Footer "Run" button
        run_button = tk.Button(
            self, text="Run Operation",
            command=self.run_operation,
            font=("Arial", 12, "bold"),
            bg="green", fg="white"
        )
        run_button.pack(pady=10)

    ##################################
    # Clone UI
    ##################################
    def build_clone_ui(self):
        lbl_desc = tk.Label(self.clone_frame,
                            text="Clone from ./core → ./<ProjectName> + npm install",
                            fg="white", bg="#1e1e2d", font=("Arial", 11))
        lbl_desc.pack(pady=5)

        form_frame = tk.Frame(self.clone_frame, bg="#1e1e2d")
        form_frame.pack(pady=5, padx=5, fill="both")

        # We'll arrange the labeled entries in a grid
        form_frame.columnconfigure(0, weight=0, minsize=180)
        form_frame.columnconfigure(1, weight=1, minsize=200)

        # Project Name
        self.add_labeled_entry(form_frame, "Project Name:", self.project_name_var, row=0)
        # remoteUrl
        self.add_labeled_entry(form_frame, "remoteUrl:", self.remote_url_var, row=1)
        # Window width
        self.add_labeled_entry(form_frame, "Window Width:", self.window_width_var, row=2)
        # Window height
        self.add_labeled_entry(form_frame, "Window Height:", self.window_height_var, row=3)
        # cacheExpirationHours
        self.add_labeled_entry(form_frame, "cacheExpirationHours:", self.cache_expiration_var, row=4)
        # customUserAgent
        self.add_labeled_entry(form_frame, "customUserAgent:", self.custom_user_agent_var, row=5)

        # Checkboxes in a grid
        checkbox_frame = tk.Frame(self.clone_frame, bg="#1e1e2d")
        checkbox_frame.pack(pady=5, fill="x")
        # Let's define 4 columns, 2 rows for the 7 checkboxes
        for c in range(4):
            checkbox_frame.columnconfigure(c, weight=1)

        # Row 0
        cb1 = self.add_checkbox(checkbox_frame, "isDeveloper", self.is_dev_var, row=0, col=0)
        cb2 = self.add_checkbox(checkbox_frame, "startMaximized", self.start_max_var, row=0, col=1)
        cb3 = self.add_checkbox(checkbox_frame, "alwaysOnTop", self.always_on_top_var, row=0, col=2)
        cb4 = self.add_checkbox(checkbox_frame, "trayEnabled", self.tray_enabled_var, row=0, col=3)

        # Row 1
        cb5 = self.add_checkbox(checkbox_frame, "disableCache", self.disable_cache_var, row=1, col=0)
        cb6 = self.add_checkbox(checkbox_frame, "hardwareAcceleration", self.hw_accel_var, row=1, col=1)

    def browse_build_folder(self):
        folder = filedialog.askdirectory(title="Select Electron Project Folder")
        if folder:
            self.build_project_folder_var.set(folder)

    ##################################
    # Build UI
    ##################################
    def build_build_ui(self):
        lbl_desc = tk.Label(
            self.build_frame,
            text="Build project with electron-builder",
            fg="white", bg="#1e1e2d", font=("Arial", 11)
        )
        lbl_desc.pack(pady=5)

        form_frame = tk.Frame(self.build_frame, bg="#1e1e2d")
        form_frame.pack(pady=5, padx=5, fill="both")

        form_frame.columnconfigure(0, weight=0, minsize=130)
        form_frame.columnconfigure(1, weight=1, minsize=200)

        # Project folder
        tk.Label(form_frame, text="Project Folder:", fg="white", bg="#1e1e2d").grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        tk.Entry(form_frame, textvariable=self.build_project_folder_var, width=30).grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        tk.Button(
            form_frame, text="Browse", bg="#007BFF", fg="white",
            command=self.browse_build_folder
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Platform
        tk.Label(form_frame, text="Platform:", fg="white", bg="#1e1e2d").grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        platform_combo = ttk.Combobox(
            form_frame, textvariable=self.build_platform_var,
            values=PLATFORMS, state="readonly", width=10
        )
        platform_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Arch
        tk.Label(form_frame, text="Architecture:", fg="white", bg="#1e1e2d").grid(
            row=2, column=0, sticky="e", padx=5, pady=5
        )
        arch_combo = ttk.Combobox(
            form_frame, textvariable=self.build_arch_var,
            values=ARCHS, state="readonly", width=10
        )
        arch_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    ##################################
    # Helpers
    ##################################
    def add_labeled_entry(self, parent, label_text, var, row):
        tk.Label(parent, text=label_text, fg="white", bg="#1e1e2d").grid(
            row=row, column=0, sticky="e", padx=5, pady=5
        )
        tk.Entry(parent, textvariable=var, width=30).grid(
            row=row, column=1, padx=5, pady=5, sticky="w"
        )

    def add_checkbox(self, parent, text, bool_var, row, col):
        chk = tk.Checkbutton(
            parent, text=text, variable=bool_var,
            fg="white", bg="#1e1e2d", selectcolor="#1e1e2d",
            onvalue=True, offvalue=False
        )
        chk.grid(row=row, column=col, padx=3, pady=3, sticky="w")
        return chk

    def update_mode_widgets(self):
        """Switch between the 'Clone' and 'Build' tab in the Notebook."""
        mode = self.mode_var.get()
        if mode == "Clone":
            self.main_notebook.select(self.clone_frame)
        else:
            self.main_notebook.select(self.build_frame)

    def run_operation(self):
        # Check which tab is currently selected
        current_tab = self.main_notebook.tab(self.main_notebook.select(), "text")
        if current_tab == "Clone Project":
            self.clone_project()
        else:
            self.build_project()


    ##################################
    # Clone Logic
    ##################################
    def clone_project(self):
        if not os.path.exists(SOURCE_FOLDER):
            messagebox.showerror("Error", f"Source folder '{SOURCE_FOLDER}' does not exist.")
            return

        project_name = self.project_name_var.get().strip()
        if not project_name:
            messagebox.showerror("Error", "Please enter a valid Project Name.")
            return

        project_dest = os.path.join(".", project_name)
        if os.path.exists(project_dest):
            confirm = messagebox.askyesno("Warning", f"'{project_dest}' already exists. Overwrite?")
            if not confirm:
                return
            shutil.rmtree(project_dest)

        try:
            # Clone
            shutil.copytree(SOURCE_FOLDER, project_dest)
            # Create settings.json
            self.create_settings_file(project_dest, project_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clone/create settings:\n{e}")
            return

        # Run npm install in thread
        threading.Thread(target=self.run_npm_install, args=(project_dest,)).start()

    def create_settings_file(self, project_dest: str, project_name: str):
        def to_int(s, default):
            try:
                return int(s)
            except:
                return default

        data = {
            "appName": project_name,
            "remoteUrl": self.remote_url_var.get().strip(),
            "windowSize": {
                "width": to_int(self.window_width_var.get(), 1024),
                "height": to_int(self.window_height_var.get(), 768),
            },
            "cacheExpirationHours": to_int(self.cache_expiration_var.get(), 24),
            "isDeveloper": self.is_dev_var.get(),
            "startMaximized": self.start_max_var.get(),
            "alwaysOnTop": self.always_on_top_var.get(),
            "trayEnabled": self.tray_enabled_var.get(),
            "customUserAgent": self.custom_user_agent_var.get().strip(),
            "disableCache": self.disable_cache_var.get(),
            "hardwareAcceleration": self.hw_accel_var.get()
        }

        settings_path = os.path.join(project_dest, "settings.json")
        package_json = os.path.join(project_dest, "package.json")

        with open(settings_path, "w", encoding="utf-8") as sf:
            json.dump(data, sf, indent=4)
            
        with open(package_json, 'r+') as rf:
            current = json.load(rf)
            current['name'] = project_name
            
            rf.seek(0)
            json.dump(current, rf, indent=4)
            rf.truncate()

    def run_npm_install(self, project_dest: str):
        self.show_progress_window("Running npm install...")

        # We'll use subprocess.Popen so we can read lines from stdout/stderr in real-time
        try:
            process = subprocess.Popen(
                ["npm", "install"],
                cwd=project_dest,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Start thread to read output
            threading.Thread(target=self.read_subprocess_output, args=(process,)).start()

            # Wait for process to finish
            return_code = process.wait()

            # After finishing, remove spinner and show result
            if return_code == 0:
                self.hide_progress_window()
                messagebox.showinfo(
                    "Success",
                    f"Cloned '{SOURCE_FOLDER}' → '{project_dest}' and installed Node modules!"
                )
            else:
                self.hide_progress_window()
                messagebox.showerror("Error", f"npm install failed. Return code: {return_code}")

        except Exception as e:
            self.hide_progress_window()
            messagebox.showerror("Error", f"npm install failed:\n{e}")
    ##################################
    # Build Logic
    ##################################
    def build_project(self):
        project_folder = self.build_project_folder_var.get().strip()
        if not os.path.exists(project_folder):
            messagebox.showerror("Error", f"'{project_folder}' does not exist.")
            return

        platform_choice = self.build_platform_var.get().strip()
        arch_choice = self.build_arch_var.get().strip()

        if not messagebox.askyesno(
            "Confirm Build",
            f"Build for {platform_choice}/{arch_choice} in '{project_folder}'?"
        ):
            return

            
        cmd = [
            "npx", "electron-builder",
            f"--{platform_choice}",
            f"--{arch_choice}",
        ]

        threading.Thread(target=self.run_build, args=(cmd, project_folder)).start()

    def run_build(self, cmd, project_folder):
        self.show_progress_window("Building with electron-builder...")

        try:
            process = subprocess.Popen(
                cmd,
                cwd=project_folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Start thread to read output
            threading.Thread(target=self.read_subprocess_output, args=(process,)).start()

            return_code = process.wait()
            if return_code == 0:
                self.hide_progress_window()
                messagebox.showinfo("Success", "Build completed successfully! Check your dist/ folder.")
            else:
                self.hide_progress_window()
                messagebox.showerror("Error", f"Build failed with return code: {return_code}")

        except Exception as e:
            self.hide_progress_window()
            messagebox.showerror("Error", f"Build failed:\n{e}")

    ##################################
    # Progress Window
    ##################################
    def show_progress_window(self, message: str):
        if self.progress_window:
            return
        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Please Wait")
        self.progress_window.configure(bg="#1e1e2d")

        self.progress_window.grab_set()

        width, height = 400, 250
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        self.progress_window.geometry(f"{width}x{height}+{x}+{y}")

        self.progress_label = tk.Label(self.progress_window, text=message, fg="white", bg="#1e1e2d")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(
            self.progress_window, orient="horizontal", mode="indeterminate", length=200
        )
        self.progress_bar.pack()
        self.progress_bar.start(10)
        
        # Text box for console output
        self.console_text = tk.Text(
            self.progress_window, wrap="word", height=10, width=50,
            bg="#222222", fg="white", font=("Consolas", 10)
        )
        self.console_text.pack(padx=5, pady=5, fill="both", expand=True)

        # Keep queue empty
        with self.output_queue.mutex:
            self.output_queue.queue.clear()

        # Schedule periodic check for new lines in queue
        self.check_output_queue()
        
    def check_output_queue(self):
        """Checks for new output lines in the queue and appends them to the console_text."""
        try:
            while True:
                line = self.output_queue.get_nowait()  # get line if available
                self.console_text.insert("end", line)
                self.console_text.see("end")  # auto-scroll
        except Empty:
            pass
        # re-schedule
        if self.progress_window:
            self.after(100, self.check_output_queue)

    def hide_progress_window(self):
        if self.progress_window:
            self.progress_bar.stop()
            self.progress_window.destroy()
            self.progress_window = None
            
    def read_subprocess_output(self, process):
        """
        Read lines from stdout/stderr in a loop and push them to output_queue,
        so we can display them in the GUI.
        """
        # Read stdout
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                self.output_queue.put(line)
            process.stdout.close()

        # Read stderr
        if process.stderr:
            for line in iter(process.stderr.readline, ''):
                if not line:
                    break
                self.output_queue.put(line)
            process.stderr.close()

##################################
# Entry point
##################################
if __name__ == "__main__":
    app = BitmatoHyperfyGUI()
    app.mainloop()
