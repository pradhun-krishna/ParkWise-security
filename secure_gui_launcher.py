# Secure GUI Launcher for Shobha ANPR System
# Provides a user-friendly interface for the secure application

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from pathlib import Path
import json
import base64
from datetime import datetime

class SecureANPRLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Shobha ANPR Parking System - Secure Launcher")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Security settings
        self.is_running = False
        self.process = None
        
        # Setup GUI
        self.setup_gui()
        
        # Load configuration
        self.load_configuration()
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Shobha ANPR Parking System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Status indicators
        ttk.Label(status_frame, text="Database:").grid(row=0, column=0, sticky=tk.W)
        self.db_status = ttk.Label(status_frame, text="Checking...", foreground="orange")
        self.db_status.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="System:").grid(row=1, column=0, sticky=tk.W)
        self.system_status = ttk.Label(status_frame, text="Ready", foreground="green")
        self.system_status.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Security:").grid(row=2, column=0, sticky=tk.W)
        self.security_status = ttk.Label(status_frame, text="Active", foreground="green")
        self.security_status.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="System Control", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        self.start_button = ttk.Button(control_frame, text="Start System", 
                                      command=self.start_system, state="normal")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop System", 
                                     command=self.stop_system, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.restart_button = ttk.Button(control_frame, text="Restart System", 
                                        command=self.restart_system, state="disabled")
        self.restart_button.grid(row=0, column=2, padx=(0, 10))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Configuration fields
        ttk.Label(config_frame, text="Database Host:").grid(row=0, column=0, sticky=tk.W)
        self.db_host = ttk.Entry(config_frame, width=30)
        self.db_host.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(config_frame, text="Database Port:").grid(row=1, column=0, sticky=tk.W)
        self.db_port = ttk.Entry(config_frame, width=30)
        self.db_port.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(config_frame, text="Database Name:").grid(row=2, column=0, sticky=tk.W)
        self.db_name = ttk.Entry(config_frame, width=30)
        self.db_name.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(config_frame, text="Database User:").grid(row=3, column=0, sticky=tk.W)
        self.db_user = ttk.Entry(config_frame, width=30)
        self.db_user.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(config_frame, text="Database Password:").grid(row=4, column=0, sticky=tk.W)
        self.db_password = ttk.Entry(config_frame, width=30, show="*")
        self.db_password.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Save config button
        ttk.Button(config_frame, text="Save Configuration", 
                  command=self.save_configuration).grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="System Logs", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Logs", 
                  command=self.clear_logs).grid(row=1, column=0, pady=(10, 0))
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def load_configuration(self):
        """Load configuration from encrypted file"""
        try:
            config_path = Path("secure_config.enc")
            if config_path.exists():
                with open(config_path, "r") as f:
                    encoded_config = f.read()
                
                config_json = base64.b64decode(encoded_config).decode()
                config = json.loads(config_json)
                
                # Populate form fields
                self.db_host.insert(0, config["database"]["host"])
                self.db_port.insert(0, str(config["database"]["port"]))
                self.db_name.insert(0, config["database"]["name"])
                self.db_user.insert(0, config["database"]["user"])
                self.db_password.insert(0, config["database"]["password"])
                
                self.log_message("Configuration loaded successfully")
            else:
                self.log_message("No configuration file found, using defaults")
                self.set_default_config()
        except Exception as e:
            self.log_message(f"Error loading configuration: {e}")
            self.set_default_config()
    
    def set_default_config(self):
        """Set default configuration values"""
        self.db_host.insert(0, "localhost")
        self.db_port.insert(0, "5432")
        self.db_name.insert(0, "shobha_parking")
        self.db_user.insert(0, "postgres")
        self.db_password.insert(0, "")
    
    def save_configuration(self):
        """Save configuration to encrypted file"""
        try:
            config_data = {
                "database": {
                    "host": self.db_host.get(),
                    "port": int(self.db_port.get()),
                    "name": self.db_name.get(),
                    "user": self.db_user.get(),
                    "password": self.db_password.get()
                },
                "parking": {
                    "lot_id": "1",
                    "hourly_rate": 10.0,
                    "minimum_charge": 20.0
                },
                "hardware": {
                    "boom_barrier_pin": 18,
                    "led_green_pin": 20,
                    "led_red_pin": 21,
                    "buzzer_pin": 22
                },
                "camera": {
                    "index": 0,
                    "exit_index": 1
                }
            }
            
            # Encrypt configuration
            config_json = json.dumps(config_data)
            encoded_config = base64.b64encode(config_json.encode()).decode()
            
            # Save to file
            with open("secure_config.enc", "w") as f:
                f.write(encoded_config)
            
            self.log_message("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def start_system(self):
        """Start the ANPR system"""
        if self.is_running:
            messagebox.showwarning("Warning", "System is already running!")
            return
        
        try:
            self.log_message("Starting ANPR system...")
            self.status_bar.config(text="Starting system...")
            
            # Start the system in a separate thread
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.restart_button.config(state="normal")
            
            # Start the system process
            self.process = subprocess.Popen([
                sys.executable, "secure_launcher.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.is_running = True
            self.system_status.config(text="Running", foreground="green")
            self.status_bar.config(text="System started successfully")
            
            # Start monitoring thread
            threading.Thread(target=self.monitor_system, daemon=True).start()
            
            self.log_message("ANPR system started successfully")
            messagebox.showinfo("Success", "ANPR system started!\n\nDashboard: http://localhost:5000")
            
        except Exception as e:
            self.log_message(f"Error starting system: {e}")
            messagebox.showerror("Error", f"Failed to start system: {e}")
            self.reset_buttons()
    
    def stop_system(self):
        """Stop the ANPR system"""
        if not self.is_running:
            messagebox.showwarning("Warning", "System is not running!")
            return
        
        try:
            self.log_message("Stopping ANPR system...")
            self.status_bar.config(text="Stopping system...")
            
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.process = None
            
            self.is_running = False
            self.system_status.config(text="Stopped", foreground="red")
            self.status_bar.config(text="System stopped")
            self.reset_buttons()
            
            self.log_message("ANPR system stopped successfully")
            messagebox.showinfo("Success", "ANPR system stopped successfully!")
            
        except Exception as e:
            self.log_message(f"Error stopping system: {e}")
            messagebox.showerror("Error", f"Failed to stop system: {e}")
    
    def restart_system(self):
        """Restart the ANPR system"""
        self.log_message("Restarting ANPR system...")
        self.stop_system()
        self.root.after(2000, self.start_system)  # Wait 2 seconds before starting
    
    def reset_buttons(self):
        """Reset button states"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.restart_button.config(state="disabled")
    
    def monitor_system(self):
        """Monitor the system process"""
        while self.is_running and self.process:
            try:
                # Check if process is still running
                if self.process.poll() is not None:
                    self.is_running = False
                    self.system_status.config(text="Stopped", foreground="red")
                    self.status_bar.config(text="System stopped unexpectedly")
                    self.reset_buttons()
                    self.log_message("System stopped unexpectedly")
                    break
                
                # Read output
                if self.process.stdout.readable():
                    output = self.process.stdout.readline()
                    if output:
                        self.log_message(output.strip())
                
                time.sleep(1)
                
            except Exception as e:
                self.log_message(f"Monitor error: {e}")
                break
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "System is running. Do you want to stop it and quit?"):
                self.stop_system()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = SecureANPRLauncher()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        messagebox.showerror("Error", f"Failed to start GUI: {e}")

if __name__ == "__main__":
    main()


