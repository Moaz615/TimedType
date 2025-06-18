import tkinter as tk
import threading
import time
import pyautogui
import keyboard
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pynput import mouse

# Optional tray icon dependencies
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Check for opencv-python (required for image targeting)
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

class TimedTyper:
    def __init__(self, root):
        self.root = root
        self.root.title("Timed Typer - Type into Any Application (Debug)")
        self.root.geometry("600x600")
        self.root.configure(bg="#2d2d2d")
        self.typing_thread = None
        self.is_typing = False
        self.stop_typing = False
        self.target_position = None
        self.image_target_path = None
        self.click_target_position = None
        self.click_target_set = False  # New flag to track if click target is already set
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        self.debug_var = tk.BooleanVar(value=True)  # Initialize debug_var early
        self.debug_print(f"PyAutoGUI version: {pyautogui.__version__}")
        self.debug_print(f"Screen size: {pyautogui.size()}")
        self.debug_print(f"Current mouse position: {pyautogui.position()}")
        self.setup_ui()
        self.setup_tray_icon()
        self.debug_print("Registering hotkey: Ctrl+Shift+S")
        keyboard.add_hotkey("ctrl+shift+s", self.hotkey_stop_typing)

    def setup_ui(self):
        title = tk.Label(self.root, text="⌨️ Timed Typer (Debug)", font=("Arial", 20, "bold"), fg='#ffffff', bg='#2d2d2d')
        title.pack(pady=10)
        subtitle = tk.Label(self.root, text="Type text at controlled speed into any application", font=("Arial", 10), fg='#cccccc', bg='#2d2d2d')
        subtitle.pack(pady=(0, 20))
        debug_cb = tk.Checkbutton(self.root, text="Debug Mode (console output)", variable=self.debug_var, fg='#cccccc', bg='#2d2d2d', selectcolor='#404040', activebackground='#2d2d2d', activeforeground='#ffffff')
        debug_cb.pack()
        tk.Label(self.root, text="Text to Type:", font=("Arial", 12, "bold"), fg='#ffffff', bg='#2d2d2d').pack(anchor='w', padx=20)
        self.text_area = scrolledtext.ScrolledText(self.root, height=6, font=("Consolas", 11), bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        self.text_area.pack(padx=20, pady=(5, 10), fill='both', expand=True)
        sample_btn = tk.Button(self.root, text="Load Sample Text", command=self.load_sample_text, bg='#404040', fg='#ffffff', relief='flat')
        sample_btn.pack(pady=(0, 10))
        import_btn = tk.Button(self.root, text="Import Text from File", command=self.import_text_from_file, bg='#404040', fg='#ffffff', relief='flat')
        import_btn.pack(pady=(0, 10))
        test_btn = tk.Button(self.root, text="Test PyAutoGUI (types 'Hello')", command=self.test_typing, bg='#28a745', fg='#ffffff', relief='flat')
        test_btn.pack(pady=(0, 10))
        controls_frame = tk.Frame(self.root, bg='#2d2d2d')
        controls_frame.pack(padx=20, pady=10, fill='x')

        # Time input with unit selection
        time_input_frame = tk.Frame(controls_frame, bg='#2d2d2d')
        time_input_frame.pack(side='left', fill='x', expand=True)
        tk.Label(time_input_frame, text="Total Time:", font=("Arial", 10), fg='#ffffff', bg='#2d2d2d').pack(anchor='w')
        time_entry_frame = tk.Frame(time_input_frame, bg='#2d2d2d')
        time_entry_frame.pack(anchor='w')
        self.time_var = tk.StringVar(value="10")
        time_entry = tk.Entry(time_entry_frame, textvariable=self.time_var, width=10, bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        time_entry.pack(side='left', pady=(2, 0))
        self.time_unit_var = tk.StringVar(value="seconds")
        time_unit_options = ["seconds", "minutes", "hours"]
        time_unit_menu = ttk.Combobox(time_entry_frame, textvariable=self.time_unit_var, values=time_unit_options, width=8, state="readonly")
        time_unit_menu.pack(side='left', padx=(5, 0), pady=(2, 0))
        time_unit_menu.set("seconds") # Default value

        delay_frame = tk.Frame(controls_frame, bg='#2d2d2d')
        delay_frame.pack(side='right', fill='x', expand=True)
        tk.Label(delay_frame, text="Delay (seconds):", font=("Arial", 10), fg='#ffffff', bg='#2d2d2d').pack(anchor='e')
        self.delay_var = tk.StringVar(value="3")
        delay_entry = tk.Entry(delay_frame, textvariable=self.delay_var, width=10, bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        delay_entry.pack(anchor='e', pady=(2, 0))
        repeat_frame = tk.Frame(self.root, bg='#2d2d2d')
        repeat_frame.pack(padx=20, pady=(5, 0), fill='x')
        tk.Label(repeat_frame, text="Repeat Count:", font=("Arial", 10), fg='#ffffff', bg='#2d2d2d').pack(side='left')
        self.repeat_var = tk.StringVar(value="1")
        repeat_entry = tk.Entry(repeat_frame, textvariable=self.repeat_var, width=5, bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        repeat_entry.pack(side='left', padx=(5, 20))
        tk.Label(repeat_frame, text="Pause Between (s):", font=("Arial", 10), fg='#ffffff', bg='#2d2d2d').pack(side='left')
        self.pause_var = tk.StringVar(value="1")
        pause_entry = tk.Entry(repeat_frame, textvariable=self.pause_var, width=5, bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        pause_entry.pack(side='left', padx=(5, 0))
        image_btn = tk.Button(self.root, text="Select Target by Image", command=self.select_image_target, bg='#404040', fg='#ffffff', relief='flat')
        image_btn.pack(pady=(0, 10))
        method_frame = tk.Frame(self.root, bg='#2d2d2d')
        method_frame.pack(padx=20, pady=10)
        tk.Label(method_frame, text="Target Selection:", font=("Arial", 10, "bold"), fg='#ffffff', bg='#2d2d2d').pack(anchor='w')
        self.method_var = tk.StringVar(value="current")
        method_options = [
            ("current", "Type at current cursor position"),
            ("click", "Type at saved click position (select once, reuse until reset)"),
            ("center", "Type at center of screen"),
            ("image", "Find target by image (screenshot)")
        ]
        for value, text in method_options:
            rb = tk.Radiobutton(method_frame, text=text, variable=self.method_var, value=value, fg='#cccccc', bg='#2d2d2d', selectcolor='#404040', activebackground='#2d2d2d', activeforeground='#ffffff')
            rb.pack(anchor='w', padx=20)
        
        self.click_status_var = tk.StringVar(value="Click target: Not set (will ask for click on first use)")
        click_status_label = tk.Label(self.root, textvariable=self.click_status_var, font=("Arial", 9), fg='#ffc107', bg='#2d2d2d')
        click_status_label.pack(pady=(0, 5))
        
        reset_btn = tk.Button(self.root, text="Reset Click Target", command=self.reset_click_target, bg='#404040', fg='#ffffff', relief='flat')
        reset_btn.pack(pady=(0, 10))
        button_frame = tk.Frame(self.root, bg='#2d2d2d')
        button_frame.pack(pady=20)
        self.start_btn = tk.Button(button_frame, text="Start Typing", command=self.start_typing, bg='#007acc', fg='#ffffff', font=("Arial", 12, "bold"), padx=20, pady=10, relief='flat')
        self.start_btn.pack(side='left', padx=10)
        self.stop_btn = tk.Button(button_frame, text="Stop Typing", command=self.stop_typing_action, bg='#d73a49', fg='#ffffff', font=("Arial", 12, "bold"), padx=20, pady=10, relief='flat', state='disabled')
        self.stop_btn.pack(side='left', padx=10)
        self.status_var = tk.StringVar(value="Ready to type")
        status_label = tk.Label(self.root, textvariable=self.status_var, font=("Arial", 10), fg='#28a745', bg='#2d2d2d')
        status_label.pack(pady=10)
        instructions = tk.Label(self.root, text="Hotkey: Ctrl+Shift+S to stop typing\n⚠️ Failsafe: Move mouse to top-left corner as backup\nInstructions: 1) Test typing 2) Enter/import text 3) Choose target (click mode saves position until reset) 4) Start", font=("Arial", 9), fg='#ffc107', bg='#2d2d2d', wraplength=550)
        instructions.pack(pady=10, padx=20)

    def debug_print(self, message):
        if hasattr(self, 'debug_var') and self.debug_var.get():
            print(f"[DEBUG] {message}")

    def test_typing(self):
        self.debug_print("Starting typing test...")
        def test_thread():
            try:
                self.status_var.set("Test: Countdown 3 seconds...")
                for i in range(3, 0, -1):
                    self.status_var.set(f"Test: {i} seconds...")
                    time.sleep(1)
                self.status_var.set("Test: Typing 'Hello'")
                self.debug_print("About to type 'Hello'")
                for char in "Hello":
                    self.debug_print(f"Typing character: '{char}'")
                    pyautogui.write(char, interval=0.1)
                    time.sleep(0.2)
                self.status_var.set("Test completed!")
                self.debug_print("Test completed successfully")
            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                self.status_var.set(error_msg)
                self.debug_print(error_msg)
                print(f"[ERROR] {e}")
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()

    def load_sample_text(self):
        sample = """Hello World!\nThis is a test of the timed typer.\nLet's see if it works correctly."""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, sample)

    def import_text_from_file(self):
        file_path = filedialog.askopenfilename(title="Select Text File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                self.debug_print(f"Imported text from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import file: {e}")
                self.debug_print(f"Failed to import file: {e}")

    def select_image_target(self):
        if not OPENCV_AVAILABLE:
            messagebox.showerror("Error", "Image targeting requires opencv-python. Install it with 'pip install opencv-python'.")
            self.debug_print("opencv-python not available")
            return
        file_path = filedialog.askopenfilename(title="Select Target Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All Files", "*.*")])
        if file_path:
            self.image_target_path = file_path
            self.method_var.set("image")
            self.debug_print(f"Selected image for targeting: {file_path}")
        else:
            self.image_target_path = None
            self.debug_print("No image selected for targeting")

    def start_typing(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            messagebox.showerror("Error", "Please enter some text to type!")
            return
        try:
            total_time_raw = float(self.time_var.get())
            time_unit = self.time_unit_var.get()
            if time_unit == "minutes":
                total_time = total_time_raw * 60
            elif time_unit == "hours":
                total_time = total_time_raw * 3600
            else: # seconds
                total_time = total_time_raw

            delay = int(self.delay_var.get())
            repeat_count = int(self.repeat_var.get())
            pause_between = float(self.pause_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for total time, delay, repeat, and pause!")
            return
        
        # Validation for total_time (now in seconds)
        if total_time <= 0 or total_time > 3600 * 24: # Allow up to 24 hours
            messagebox.showerror("Error", "Total time must be between 1 second and 24 hours!")
            return
        if delay < 0 or delay > 60:
            messagebox.showerror("Error", "Delay must be between 0 and 60 seconds!")
            return
        if repeat_count < 1 or repeat_count > 100:
            messagebox.showerror("Error", "Repeat count must be between 1 and 100!")
            return
        if pause_between < 0 or pause_between > 60:
            messagebox.showerror("Error", "Pause must be between 0 and 60 seconds!")
            return
        self.debug_print(f"Starting typing process: {len(text)} characters over {total_time} seconds, repeat {repeat_count}x, pause {pause_between}s")
        self.is_typing = True
        self.stop_typing = False
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.typing_thread = threading.Thread(target=self.typing_process, args=(text, total_time, delay, repeat_count, pause_between))
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def typing_process(self, text, total_time, delay, repeat_count, pause_between):
        try:
            self.debug_print("Typing process started")
            for i in range(delay, 0, -1):
                if self.stop_typing:
                    return
                self.status_var.set(f"Get ready! Countdown: {i} seconds...")
                self.debug_print(f"Countdown: {i}")
                time.sleep(1)
            if self.stop_typing:
                return
            method = self.method_var.get()
            self.debug_print(f"Using method: {method}")
            if method == "current":
                self.target_position = pyautogui.position()
                self.status_var.set("Using current cursor position...")
                self.debug_print(f"Current position: {self.target_position}")
            elif method == "center":
                screen_width, screen_height = pyautogui.size()
                self.target_position = (screen_width // 2, screen_height // 2)
                self.status_var.set("Using center of screen...")
                self.debug_print(f"Center position: {self.target_position}")
            elif method == "click":
                # Only wait for click if no position is already set
                if not self.click_target_set:
                    self.status_var.set("Left-click target to select position! (5 seconds)")
                    self.click_target_position = self.wait_for_click(5)
                    if self.click_target_position is None:
                        self.status_var.set("No click detected - operation cancelled")
                        self.debug_print("No click detected")
                        return
                    else:
                        self.click_target_set = True  # Mark as set PERMANENTLY
                        self.status_var.set(f"Click position saved permanently: {self.click_target_position}")
                        self.debug_print(f"Click position saved permanently: {self.click_target_position}")
                        self.update_click_status()
                else:
                    self.status_var.set(f"Using permanently saved click position: {self.click_target_position}")
                    self.debug_print(f"Using permanently saved click position: {self.click_target_position}")
                self.target_position = self.click_target_position
            elif method == "image":
                if not OPENCV_AVAILABLE:
                    self.status_var.set("Image targeting unavailable: opencv-python not installed!")
                    self.debug_print("opencv-python not installed")
                    return
                if hasattr(self, 'image_target_path') and self.image_target_path:
                    self.status_var.set("Locating target by image...")
                    self.debug_print(f"Locating on screen: {self.image_target_path}")
                    location = pyautogui.locateCenterOnScreen(self.image_target_path, confidence=0.8)
                    if location:
                        self.target_position = (location.x, location.y)
                        self.status_var.set("Found image target on screen.")
                        self.debug_print(f"Image target found at: {self.target_position}")
                    else:
                        self.status_var.set("Image target not found on screen!")
                        self.debug_print("Image target not found!")
                        return
                else:
                    self.status_var.set("No image selected for targeting!")
                    self.debug_print("No image selected for targeting!")
                    return
            if self.target_position:
                for rep in range(repeat_count):
                    if self.stop_typing:
                        break
                    self.status_var.set(f"Typing run {rep+1} of {repeat_count}")
                    self.debug_print(f"Starting repeat run {rep+1}/{repeat_count} at position: {self.target_position}")
                    self.type_text(text, total_time)
                    if rep < repeat_count - 1 and not self.stop_typing:
                        self.status_var.set(f"Pause between runs: {pause_between}s")
                        self.debug_print(f"Pause between runs: {pause_between}s")
                        time.sleep(pause_between)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.status_var.set(error_msg)
            self.debug_print(error_msg)
            print(f"[ERROR] {e}")
        finally:
            self.cleanup()

    def type_text(self, text, total_time):
        if self.stop_typing or self.target_position is None:
            return
        self.debug_print(f"Starting to type at position: {self.target_position}")
        try:
            pyautogui.moveTo(self.target_position[0], self.target_position[1], duration=0.1)
            pyautogui.click()
            self.debug_print(f"Clicked at {self.target_position}")
            time.sleep(0.5)
        except Exception as e:
            error_msg = f"Click error: {str(e)}"
            self.status_var.set(error_msg)
            self.debug_print(error_msg)
            return
        num_chars = len(text)
        interval = total_time / num_chars if num_chars > 0 else 0.1
        self.debug_print(f"Typing interval: {interval:.3f} seconds per character")
        self.status_var.set("Typing started...")
        for i, char in enumerate(text):
            if self.stop_typing:
                self.debug_print("Typing stopped by user")
                break
            try:
                if char == '\n':
                    self.debug_print("Typing: ENTER")
                    pyautogui.press('enter')
                elif char == '\t':
                    self.debug_print("Typing: TAB")
                    pyautogui.press('tab')
                else:
                    self.debug_print(f"Typing character: '{char}' (ord: {ord(char)})")
                    pyautogui.write(char, interval=0)
                progress = f"Typing: {i+1}/{num_chars} ({((i+1)/num_chars*100):.1f}%)"
                self.status_var.set(progress)
                if i < num_chars - 1:
                    time.sleep(interval)
            except Exception as e:
                error_msg = f"Typing error at character {i} ('{char}'): {str(e)}"
                self.status_var.set(error_msg)
                self.debug_print(error_msg)
                print(f"[ERROR] {e}")
                break
        if not self.stop_typing:
            self.status_var.set("Typing completed successfully!")
            self.debug_print("Typing completed successfully")
        else:
            self.status_var.set("Typing stopped by user.")

    def wait_for_click(self, timeout_seconds):
        self.debug_print(f"Waiting for click for {timeout_seconds} seconds")
        self.root.withdraw()
        click_position = [None]  # Mutable to store position from listener
        click_captured = [False]  # Flag to ensure only first click is captured
        
        def on_click(x, y, button, pressed):
            if button == mouse.Button.left and not pressed and not click_captured[0]:  # Only capture first click
                self.debug_print(f"First left-click detected at: ({x}, {y})")
                click_position[0] = (x, y)
                click_captured[0] = True  # Mark that we've captured the click
                return False  # Stop listener
            elif button == mouse.Button.left and not pressed and click_captured[0]:
                self.debug_print(f"Ignoring additional click at: ({x}, {y})")
                return False # Stop listener after first click is captured
            return True  # Continue listening
        
        listener = mouse.Listener(on_click=on_click)
        listener.start()
        try:
            start_time = time.time() 
            while time.time() - start_time < timeout_seconds and not self.stop_typing:
                if click_position[0] is not None:
                    self.debug_print("First click captured, ignoring any subsequent clicks")
                    return click_position[0]
                remaining = int(timeout_seconds - (time.time() - start_time))
                if remaining >= 0:
                    self.status_var.set(f"Left-click target to select position! ({remaining}s remaining)")
                time.sleep(0.05)
            self.debug_print("No click detected within timeout")
            return None
        finally:
            listener.stop()
            self.root.deiconify()

    def stop_typing_action(self):
        self.debug_print("Stop button pressed")
        self.debug_print("Stop button pressed")
        self.stop_typing = True
        self.cleanup()
        self.status_var.set("Operation stopped.")

    def cleanup(self):
        self.debug_print("Cleaning up...")
        self.is_typing = False
        self.target_position = None  # Clear target_position but PRESERVE click_target_position and click_target_set
        self.root.after(0, self.reset_ui)
        try:
            self.root.deiconify()
        except:
            pass

    def reset_ui(self):
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def setup_tray_icon(self):
        if not TRAY_AVAILABLE:
            self.debug_print("pystray or PIL not available, tray icon disabled.")
            return
        image = Image.new('RGB', (64, 64), color=(40, 122, 204))
        d = ImageDraw.Draw(image)
        d.text((10, 20), "TT", fill=(255, 255, 255))
        menu = (
            pystray.MenuItem('Show/Hide', self.toggle_window),
            pystray.MenuItem('Exit', self.exit_app)
        )
        self.tray_icon = pystray.Icon("TimedTyper", image, "Timed Typer", menu)
        self.debug_print("Starting system tray icon")
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def toggle_window(self, icon=None, item=None):
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
        else:
            self.root.withdraw()
        self.debug_print("Toggled window visibility")

    def exit_app(self, icon=None, item=None):
        self.debug_print("Exiting app via tray icon")
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        keyboard.remove_hotkey('ctrl+shift+s')
        self.debug_print("Removed hotkey: Ctrl+Shift+S")
        self.root.quit()

    def hotkey_stop_typing(self):
        self.debug_print('Global hotkey pressed to stop typing')
        self.stop_typing_action()

    def reset_click_target(self):
        self.click_target_position = None
        self.click_target_set = False  # Reset the flag
        self.update_click_status()
        self.status_var.set("Click target position reset. Select a new position for click mode.")
        self.debug_print("Click target position reset.")

    def update_click_status(self):
        """Update the click status label to show current state"""
        if self.click_target_set and self.click_target_position:
            self.click_status_var.set(f"Click target: PERMANENTLY SET at ({self.click_target_position[0]}, {self.click_target_position[1]})")
        else:
            self.click_status_var.set("Click target: Not set (will ask for click on first use)")

if __name__ == "__main__":
    print("Starting Timed Typer Debug Version...")
    print("Check console for debug output when 'Debug Mode' is enabled")
    print("=" * 50)
    root = tk.Tk()
    app = TimedTyper(root)
    root.mainloop()
print("I love You!")