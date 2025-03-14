"""
GUI interface for webpage monitor
"""
import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional
from webpage_monitor import WebpageMonitor
from PIL import Image, ImageTk
import base64
import io

class MonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Webpage Monitor")
        self.monitor: Optional[WebpageMonitor] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False

        # URL Entry
        url_frame = ttk.Frame(root, padding="5")
        url_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky="w")
        self.url_var = tk.StringVar(value="https://example.com")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, padx=5)

        # Interval Entry
        interval_frame = ttk.Frame(root, padding="5")
        interval_frame.grid(row=1, column=0, sticky="ew")
        ttk.Label(interval_frame, text="Interval (seconds):").grid(row=0, column=0, sticky="w")
        self.interval_var = tk.StringVar(value="60")
        self.interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=0, column=1, padx=5)

        # Preview Area
        preview_frame = ttk.LabelFrame(root, text="Page Preview", padding="5")
        preview_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        # Status Display
        status_frame = ttk.LabelFrame(root, text="Status", padding="5")
        status_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        self.status_var = tk.StringVar(value="Not monitoring")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")

        # Latest Result Display
        result_frame = ttk.LabelFrame(root, text="Latest Result", padding="5")
        result_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        self.result_var = tk.StringVar(value="No results yet")
        self.result_label = ttk.Label(result_frame, textvariable=self.result_var, wraplength=400)
        self.result_label.grid(row=0, column=0, sticky="w")

        # Control Buttons
        button_frame = ttk.Frame(root, padding="5")
        button_frame.grid(row=5, column=0, sticky="ew")
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)  # Make preview area expandable

    def update_preview(self, screenshot_base64: Optional[str]):
        """Update the preview image"""
        if screenshot_base64:
            try:
                # Convert base64 to PIL Image
                image_data = base64.b64decode(screenshot_base64)
                image = Image.open(io.BytesIO(image_data))

                # Resize to fit window (maintain aspect ratio)
                preview_width = 800
                ratio = preview_width / image.width
                preview_height = int(image.height * ratio)
                image = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(image)
                self.preview_label.configure(image=photo)
                self.preview_label.image = photo  # Keep reference
            except Exception as e:
                self.update_status(f"Error updating preview: {str(e)}")
        else:
            self.preview_label.configure(image='')

    def update_status(self, status: str):
        """Update the status display"""
        self.status_var.set(status)
        self.root.update_idletasks()

    def update_result(self, result: str):
        """Update the result display"""
        self.result_var.set(result)
        self.root.update_idletasks()

    def monitoring_loop(self):
        """Background monitoring loop"""
        try:
            while self.is_monitoring:
                result = self.monitor.check_for_changes()
                if result['status'] == 'error':
                    self.update_status(f"Error: {result['message']}")
                elif result['status'] == 'changed':
                    self.update_status("Change detected!")
                    self.update_result(f"Content changed")
                elif result['status'] == 'initial':
                    self.update_status("Initial content captured")
                    self.update_result("Initial content captured")
                else:
                    self.update_status("Monitoring...")
                    self.update_result("No changes detected")

                # Update preview
                self.update_preview(result.get('screenshot'))

                # Sleep for the specified interval
                for _ in range(int(self.interval_var.get())):
                    if not self.is_monitoring:
                        break
                    self.root.after(1000)  # Sleep for 1 second
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            if not self.is_monitoring:
                self.update_status("Monitoring stopped")

    def start_monitoring(self):
        """Start the monitoring process"""
        try:
            url = self.url_var.get()
            interval = int(self.interval_var.get())

            self.monitor = WebpageMonitor(url=url, interval=interval)
            self.is_monitoring = True

            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()

            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.DISABLED)
            self.interval_entry.config(state=tk.DISABLED)

            self.update_status("Starting monitoring...")
        except ValueError as e:
            self.update_status(f"Error: {str(e)}")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.NORMAL)

        self.update_status("Monitoring stopped")

def main():
    root = tk.Tk()
    root.title("Webpage Monitor")
    # Set initial window size
    root.geometry("800x600")
    MonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()