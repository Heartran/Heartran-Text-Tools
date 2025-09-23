import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import tempfile
import atexit
import time
from pathlib import Path

try:
    import win32api
    import win32con
    from win32api import GetSystemMetrics
    from win32con import IDI_APPLICATION, IDI_INFORMATION, IDI_WARNING, IDI_ERROR
    from win32con import SM_CXSMICON, SM_CYSMICON
    from win32gui import CreateWindowEx, SendMessage, LoadImage, IMAGE_ICON, LR_LOADFROMFILE
    from win32gui import WM_SETICON, ICON_SMALL, ICON_BIG, DestroyIcon
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class ToolLock:
    """Class to handle tool locking to prevent multiple instances"""
    _instance = None
    _locks = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolLock, cls).__new__(cls)
            cls._temp_dir = tempfile.gettempdir()
            atexit.register(cls.cleanup)
        return cls._instance
    
    @classmethod
    def is_locked(cls, tool_name):
        """Check if a tool is already running"""
        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        if os.path.exists(lock_file):
            # Check if the process is still running
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process exists
                try:
                    os.kill(pid, 0)  # Doesn't kill the process, just checks if it exists
                    return True
                except (ProcessLookupError, PermissionError):
                    # Process doesn't exist or we don't have permission
                    os.unlink(lock_file)
                    return False
            except (ValueError, PermissionError):
                # Lock file is invalid or we can't read it
                return False
        return False
    
    @classmethod
    def acquire_lock(cls, tool_name):
        """Acquire a lock for a tool"""
        if cls.is_locked(tool_name):
            return False
            
        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        try:
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            cls._locks[tool_name] = lock_file
            return True
        except (IOError, OSError):
            return False
    
    @classmethod
    def release_lock(cls, tool_name):
        """Release a lock for a tool"""
        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        try:
            if os.path.exists(lock_file):
                os.unlink(lock_file)
            if tool_name in cls._locks:
                del cls._locks[tool_name]
        except (IOError, OSError):
            pass
    
    @classmethod
    def cleanup(cls):
        """Clean up all locks on exit"""
        for tool_name in list(cls._locks.keys()):
            cls.release_lock(tool_name)

class TextToolsLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Heartran Text Tools")
        self.root.geometry("600x400")
        self.root.minsize(500, 350)
        
        # Set window icon if available
        try:
            self.root.iconbitmap(self.resource_path("icon.ico"))
        except:
            pass
        
        self.setup_ui()
    
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_system_icon(self, icon_id, size=16):
        if not HAS_WIN32:
            return None
            
        try:
            # Load system icon
            hicon = win32api.LoadImage(0, icon_id, win32con.IMAGE_ICON, 
                                     size, size, win32con.LR_SHARED)
            # Convert to PhotoImage
            icon = tk.PhotoImage(data=win32api.GetIconBitmap(icon_id))
            return icon
        except Exception as e:
            print(f"Error loading system icon: {e}")
            return None
    
    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.configure("TButton", font=('Segoe UI', 10), padding=10)
        style.configure("Title.TLabel", font=('Segoe UI', 16, 'bold'))
        style.configure("Desc.TLabel", font=('Segoe UI', 9))
        
        # Load system icons if available
        self.app_icon = self.get_system_icon(IDI_APPLICATION, 32)
        self.info_icon = self.get_system_icon(IDI_INFORMATION, 16)
        self.warning_icon = self.get_system_icon(IDI_WARNING, 16)
        self.error_icon = self.get_system_icon(IDI_ERROR, 16)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text="Heartran Text Tools", 
            style="Title.TLabel"
        ).pack(side=tk.LEFT)
        
        # Tools frame
        tools_frame = ttk.LabelFrame(main_frame, text="Strumenti Disponibili", padding=15)
        tools_frame.pack(fill=tk.BOTH, expand=True)
        tools_frame.columnconfigure(0, weight=1)
        
        # Tool 1: Capitalize Text
        tool1_frame = ttk.Frame(tools_frame)
        tool1_frame.grid(row=0, column=0, sticky='ew', pady=5, padx=5)
        
        btn1 = ttk.Button(
            tool1_frame, 
            text=" Capitalizza Testo",
            command=self.launch_capitalize_tool,
            style="Accent.TButton"
        )
        btn1.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add icon if available
        if hasattr(self, 'info_icon') and self.info_icon:
            btn1.configure(image=self.info_icon, compound=tk.LEFT)
        
        ttk.Label(
            tool1_frame,
            text="Converte il testo negli appunti in maiuscole/minuscole intelligenti",
            style="Desc.TLabel"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Tool 2: Uppercase Text
        tool2_frame = ttk.Frame(tools_frame)
        tool2_frame.grid(row=1, column=0, sticky='ew', pady=5, padx=5)
        
        btn2 = ttk.Button(
            tool2_frame, 
            text=" MAIUSCOLO",
            command=self.launch_uppercase_tool,
            style="Accent.TButton"
        )
        btn2.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add icon if available
        if hasattr(self, 'warning_icon') and self.warning_icon:
            btn2.configure(image=self.warning_icon, compound=tk.LEFT)
        
        ttk.Label(
            tool2_frame,
            text="Converte tutto il testo negli appunti in MAIUSCOLO",
            style="Desc.TLabel"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure style for accent button
        style.configure("Accent.TButton", 
                       font=('Segoe UI', 10, 'bold'), 
                       padding=10)
    
    def launch_tool(self, script_name):
        tool_name = os.path.splitext(script_name)[0]  # Remove .py extension for lock name
        
        # Check if tool is already running
        if ToolLock().is_locked(tool_name):
            messagebox.showinfo(
                "Strumento già in esecuzione",
                f"Lo strumento '{tool_name}' è già in esecuzione.\n"
                "Chiudere l'istanza esistente prima di aprirne una nuova."
            )
            self.status_var.set(f"{tool_name} già in esecuzione")
            return
            
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
            if os.path.exists(script_path):
                # Acquire lock before starting the tool
                if not ToolLock().acquire_lock(tool_name):
                    messagebox.showerror("Errore", f"Impossibile acquisire il lock per {tool_name}")
                    self.status_var.set("Errore di avvio")
                    return
                    
                self.status_var.set(f"Avvio di {script_name}...")
                self.root.update()
                
                # Use the same Python interpreter to run the script
                python = sys.executable
                
                def cleanup_and_launch():
                    try:
                        process = subprocess.Popen([python, script_path])
                        # Wait a bit to ensure the process starts
                        time.sleep(1)
                        if process.poll() is not None:  # Process already finished
                            ToolLock().release_lock(tool_name)
                        else:
                            # Set up a thread to monitor the process
                            def monitor_process():
                                process.wait()
                                ToolLock().release_lock(tool_name)
                            
                            import threading
                            monitor_thread = threading.Thread(target=monitor_process, daemon=True)
                            monitor_thread.start()
                            
                        self.root.after(0, lambda: self.status_var.set(f"{script_name} avviato con successo"))
                    except Exception as e:
                        ToolLock().release_lock(tool_name)
                        self.root.after(0, lambda: messagebox.showerror(
                            "Errore", 
                            f"Impossibile avviare lo strumento: {str(e)}"
                        ))
                        self.root.after(0, lambda: self.status_var.set("Errore durante l'avvio dello strumento"))
                
                # Run the launch in a separate thread to keep the UI responsive
                import threading
                threading.Thread(target=cleanup_and_launch, daemon=True).start()
                
            else:
                messagebox.showerror("Errore", f"File non trovato: {script_name}")
                self.status_var.set("Errore: file non trovato")
                
        except Exception as e:
            ToolLock().release_lock(tool_name)  # Ensure lock is released on error
            messagebox.showerror("Errore", f"Impossibile avviare lo strumento: {str(e)}")
            self.status_var.set("Errore durante l'avvio dello strumento")
    
    def launch_capitalize_tool(self):
        self.launch_tool("capitolAllText.py")
    
    def launch_uppercase_tool(self):
        self.launch_tool("upperAllText.py")

def main():
    root = tk.Tk()
    
    # Set theme colors
    root.tk_setPalette(background='#f0f0f0', foreground='black',
                      activeBackground='#e0e0e0', activeForeground='black')
    
    # Set window icon using system icon if available
    if HAS_WIN32:
        try:
            # Try to load the application icon from system
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(ico_path):
                root.iconbitmap(default=ico_path)
            else:
                # Fall back to system application icon
                root.iconbitmap(default='@default')
        except Exception as e:
            print(f"Could not set window icon: {e}")
    
    # Set window icon if available
    try:
        root.iconbitmap(default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
    except:
        pass
    
    app = TextToolsLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()