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

        # Navigation Buttons
        nav_frame = ttk.Frame(root, padding="5")
        nav_frame.grid(row=1, column=0, sticky="ew")
        self.back_button = ttk.Button(nav_frame, text="←", command=self.browser_back, width=3)
        self.back_button.grid(row=0, column=0, padx=2)
        self.forward_button = ttk.Button(nav_frame, text="→", command=self.browser_forward, width=3)
        self.forward_button.grid(row=0, column=1, padx=2)
        self.refresh_button = ttk.Button(nav_frame, text="↻", command=self.browser_refresh, width=3)
        self.refresh_button.grid(row=0, column=2, padx=2)
        self.go_button = ttk.Button(nav_frame, text="Go", command=self.navigate_to_url, width=5)
        self.go_button.grid(row=0, column=3, padx=2)

        # Interval Entry
        interval_frame = ttk.Frame(nav_frame)
        interval_frame.grid(row=0, column=4, padx=20, sticky="e")
        ttk.Label(interval_frame, text="Interval (seconds):").grid(row=0, column=0, sticky="w")
        self.interval_var = tk.StringVar(value="60")
        self.interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=0, column=1, padx=5)

        # Preview Options
        options_frame = ttk.LabelFrame(root, text="Preview Options", padding="5")
        options_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Screenshot checkbox
        self.screenshot_var = tk.BooleanVar(value=True)
        self.screenshot_cb = ttk.Checkbutton(
            options_frame, 
            text="Enable Screenshot Preview",
            variable=self.screenshot_var,
            command=self.toggle_screenshot
        )
        self.screenshot_cb.grid(row=0, column=0, sticky="w", padx=5)

        # HTML checkbox
        self.html_var = tk.BooleanVar(value=True)
        self.html_cb = ttk.Checkbutton(
            options_frame,
            text="Enable HTML Preview",
            variable=self.html_var,
            command=self.toggle_html
        )
        self.html_cb.grid(row=0, column=1, sticky="w", padx=5)

        # Interactive mode checkbox
        self.interactive_var = tk.BooleanVar(value=True)
        self.interactive_cb = ttk.Checkbutton(
            options_frame,
            text="Enable Interactive Mode",
            variable=self.interactive_var,
            command=self.toggle_interactive
        )
        self.interactive_cb.grid(row=0, column=2, sticky="w", padx=5)

        # Notebook for Preview Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        # Screenshot Preview Tab
        self.screenshot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.screenshot_frame, text="Screenshot")
        self.preview_label = ttk.Label(self.screenshot_frame)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        # HTML Preview Tab
        self.html_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.html_frame, text="HTML")
        self.html_text = tk.Text(self.html_frame, wrap=tk.WORD, height=20)
        self.html_text.grid(row=0, column=0, sticky="nsew")
        # Add scrollbar for HTML view
        html_scrollbar = ttk.Scrollbar(self.html_frame, orient="vertical", command=self.html_text.yview)
        html_scrollbar.grid(row=0, column=1, sticky="ns")
        self.html_text.configure(yscrollcommand=html_scrollbar.set)

        # Interactive Browser Tab
        self.browser_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browser_frame, text="Interactive")
        self.browser_preview = ttk.Label(self.browser_frame)
        self.browser_preview.grid(row=0, column=0, sticky="nsew")

        # Status Display
        status_frame = ttk.LabelFrame(root, text="Status", padding="5")
        status_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        self.status_var = tk.StringVar(value="Not monitoring")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")

        # Latest Result Display
        result_frame = ttk.LabelFrame(root, text="Latest Result", padding="5")
        result_frame.grid(row=5, column=0, sticky="ew", padx=5, pady=5)
        self.result_var = tk.StringVar(value="No results yet")
        self.result_label = ttk.Label(result_frame, textvariable=self.result_var, wraplength=400)
        self.result_label.grid(row=0, column=0, sticky="w")

        # Control Buttons
        button_frame = ttk.Frame(root, padding="5")
        button_frame.grid(row=6, column=0, sticky="ew")
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)  # Make preview area expandable

        # Configure frame expansion
        for frame in [self.screenshot_frame, self.html_frame, self.browser_frame]:
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

    def toggle_screenshot(self):
        """Toggle screenshot preview"""
        if not self.screenshot_var.get():
            self.notebook.tab(self.screenshot_frame, state="disabled")
        else:
            self.notebook.tab(self.screenshot_frame, state="normal")

        if self.monitor:
            self.monitor.capture_screenshot = self.screenshot_var.get()

    def toggle_html(self):
        """Toggle HTML preview"""
        if not self.html_var.get():
            self.notebook.tab(self.html_frame, state="disabled")
        else:
            self.notebook.tab(self.html_frame, state="normal")

        if self.monitor:
            self.monitor.capture_html = self.html_var.get()

    def toggle_interactive(self):
        """Toggle interactive mode"""
        if not self.interactive_var.get():
            self.notebook.tab(self.browser_frame, state="disabled")
        else:
            self.notebook.tab(self.browser_frame, state="normal")

    def browser_back(self):
        """Go back in browser history"""
        if self.monitor and self.interactive_var.get():
            self.monitor.browser_back()

    def browser_forward(self):
        """Go forward in browser history"""
        if self.monitor and self.interactive_var.get():
            self.monitor.browser_forward()

    def browser_refresh(self):
        """Refresh current page"""
        if self.monitor and self.interactive_var.get():
            self.monitor.browser_refresh()

    def navigate_to_url(self):
        """Navigate to entered URL"""
        if self.monitor and self.interactive_var.get():
            url = self.url_var.get()
            self.monitor.navigate_to(url)

    def update_preview(self, screenshot_base64: Optional[str], html_content: Optional[str]):
        """Update both screenshot and HTML previews"""
        # Update screenshot preview if enabled
        if self.screenshot_var.get() and screenshot_base64:
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

                # Update interactive browser preview if enabled
                if self.interactive_var.get():
                    browser_photo = ImageTk.PhotoImage(image)
                    self.browser_preview.configure(image=browser_photo)
                    self.browser_preview.image = browser_photo
            except Exception as e:
                self.update_status(f"Error updating preview: {str(e)}")
        else:
            self.preview_label.configure(image='')
            self.browser_preview.configure(image='')

        # Update HTML preview if enabled
        if self.html_var.get() and html_content:
            self.html_text.delete('1.0', tk.END)
            self.html_text.insert('1.0', html_content)
        else:
            self.html_text.delete('1.0', tk.END)
            self.html_text.insert('1.0', 'No HTML content available')

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
                    self.update_result("Content changed")
                elif result['status'] == 'initial':
                    self.update_status("Initial content captured")
                    self.update_result("Initial content captured")
                else:
                    self.update_status("Monitoring...")
                    self.update_result("No changes detected")

                # Update preview
                self.update_preview(result.get('screenshot'), result.get('html'))

                # Update URL if in interactive mode
                if self.interactive_var.get() and self.monitor:
                    current_url = self.monitor.get_current_url()
                    if current_url != self.url_var.get():
                        self.url_var.set(current_url)

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

            self.monitor = WebpageMonitor(
                url=url,
                interval=interval,
                capture_screenshot=self.screenshot_var.get(),
                capture_html=self.html_var.get(),
                interactive_mode=self.interactive_var.get()
            )
            self.is_monitoring = True

            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()

            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.url_entry.config(state=tk.DISABLED)
            self.interval_entry.config(state=tk.DISABLED)
            self.screenshot_cb.config(state=tk.DISABLED)
            self.html_cb.config(state=tk.DISABLED)
            self.interactive_cb.config(state=tk.DISABLED)

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
        self.screenshot_cb.config(state=tk.NORMAL)
        self.html_cb.config(state=tk.NORMAL)
        self.interactive_cb.config(state=tk.NORMAL)

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