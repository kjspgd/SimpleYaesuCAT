import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import time
import threading

class SerialConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Connection & Tuning Control")

        # Frame 1: Status Section
        self.status_frame = tk.LabelFrame(self.root, text="Status", padx=10, pady=10)
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.transmit_power_label = tk.Label(self.status_frame, text="Transmit Power:", font=("Helvetica", 12, "bold"))
        self.transmit_power_label.grid(row=0, column=0, padx=5, pady=5)
        self.transmit_power_value = tk.Label(self.status_frame, text="N/A", font=("Helvetica", 24, "bold"))  # Larger font
        self.transmit_power_value.grid(row=0, column=1, padx=5, pady=5)

        self.frequency_label = tk.Label(self.status_frame, text="Frequency:", font=("Helvetica", 12, "bold"))
        self.frequency_label.grid(row=1, column=0, padx=5, pady=5)
        self.frequency_value = tk.Label(self.status_frame, text="N/A")
        self.frequency_value.grid(row=1, column=1, padx=5, pady=5)

        self.tuning_status_label = tk.Label(self.status_frame, text="Tuning Status:", font=("Helvetica", 12, "bold"))
        self.tuning_status_label.grid(row=2, column=0, padx=5, pady=5)
        self.tuning_status_value = tk.Label(self.status_frame, text="N/A")
        self.tuning_status_value.grid(row=2, column=1, padx=5, pady=5)

        self.active_vfo_label = tk.Label(self.status_frame, text="Active VFO:", font=("Helvetica", 12, "bold"))
        self.active_vfo_label.grid(row=3, column=0, padx=5, pady=5)
        self.active_vfo_value = tk.Label(self.status_frame, text="N/A")
        self.active_vfo_value.grid(row=3, column=1, padx=5, pady=5)

        self.refresh_button = tk.Button(self.status_frame, text="Refresh", command=self.refresh_status)
        self.refresh_button.grid(row=4, columnspan=2, pady=10)

        # Frame 2: Tune Controls Section
        self.tune_frame = tk.LabelFrame(self.root, text="Tune Controls", padx=10, pady=10)
        self.tune_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tune_button = tk.Button(self.tune_frame, text="Tune", command=self.tune)
        self.tune_button.grid(row=0, columnspan=2, pady=10)

        self.transmit_power_input_label = tk.Label(self.tune_frame, text="Set Transmit Power:")
        self.transmit_power_input_label.grid(row=1, column=0, padx=5, pady=5)
        self.transmit_power_input = tk.Entry(self.tune_frame)
        self.transmit_power_input.grid(row=1, column=1, padx=5, pady=5)

        self.set_power_button = tk.Button(self.tune_frame, text="Set", command=self.set_transmit_power)
        self.set_power_button.grid(row=2, columnspan=2, pady=5)

        self.power_on_button = tk.Button(self.tune_frame, text="Power On", command=self.power_on)
        self.power_on_button.grid(row=3, column=0, pady=10)

        self.power_off_button = tk.Button(self.tune_frame, text="Power Off", command=self.power_off)
        self.power_off_button.grid(row=3, column=1, pady=10)

        # Frame 3: Serial Connection Section
        self.serial_frame = tk.LabelFrame(self.root, text="Serial Connection", padx=10, pady=10)
        self.serial_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.comm_port_label = tk.Label(self.serial_frame, text="Comm Port:")
        self.comm_port_label.grid(row=0, column=0, padx=5, pady=5)
        self.comm_port_input = tk.StringVar()
        self.comm_port_input.set(self.get_default_com_port())  # Set default COM port
        self.comm_port_menu = tk.OptionMenu(self.serial_frame, self.comm_port_input, *self.get_available_com_ports())
        self.comm_port_menu.grid(row=0, column=1, padx=5, pady=5)


        self.speed_label = tk.Label(self.serial_frame, text="Speed:")
        self.speed_label.grid(row=1, column=0, padx=5, pady=5)
        self.speed_input = tk.Entry(self.serial_frame)
        self.speed_input.grid(row=1, column=1, padx=5, pady=5)
        self.speed_input.insert(0, "4800")  # Default speed

        self.stop_bits_label = tk.Label(self.serial_frame, text="Stop Bits:")
        self.stop_bits_label.grid(row=2, column=0, padx=5, pady=5)
        self.stop_bits_input = tk.Entry(self.serial_frame)
        self.stop_bits_input.grid(row=2, column=1, padx=5, pady=5)
        self.stop_bits_input.insert(0,"1")  # Default Input

        self.parity_label = tk.Label(self.serial_frame, text="Parity:")
        self.parity_label.grid(row=3, column=0, padx=5, pady=5)
        self.parity_input = tk.StringVar()
        self.parity_input.set("None")  # Default parity
        self.parity_menu = tk.OptionMenu(self.serial_frame, self.parity_input, "None", "Even", "Odd", "Mark", "Space")
        self.parity_menu.grid(row=3, column=1, padx=5, pady=5)


        self.set_serial_button = tk.Button(self.serial_frame, text="Set", command=self.set_serial_params)
        self.set_serial_button.grid(row=4, columnspan=2, pady=10)



        # Initialize serial connection
        self.serial_lock = threading.Lock()
        self.ser = None
        self.refresh_status_thread = threading.Thread(target=self.refresh_status_periodically, daemon=True)
        self.refresh_status_thread.start()

        self.set_serial_params()

    def get_available_com_ports(self):
        # Get all available serial ports on the system
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def get_default_com_port(self):
        # Default to COM20 if available, otherwise the first available port
        available_ports = self.get_available_com_ports()
        return "COM20" if "COM20" in available_ports else available_ports[0] if available_ports else "N/A"


    def set_serial_params(self):
        """Initialize the serial connection based on the user inputs."""
        comm_port = self.comm_port_input.get()

        # Check if the speed field is empty, and set a default value if it is.
        speed_str = self.speed_input.get()
        speed = 4800  # Default speed if the input is empty
        if speed_str:
            try:
                speed = int(speed_str)
            except ValueError:
                print(f"Invalid baud rate: {speed_str}. Using default value: {speed}")

        stop_bits = int(self.stop_bits_input.get())
        parity = self.parity_input.get()

        if parity == "None":
            parity = serial.PARITY_NONE
        elif parity == "Even":
            parity = serial.PARITY_EVEN
        elif parity == "Odd":
            parity = serial.PARITY_ODD

        try:
            self.ser = serial.Serial(
                port=comm_port,
                baudrate=speed,
                stopbits=stop_bits,
                parity=parity,
                timeout=0.05
            )
            print("Serial connection established.")
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            messagebox.showerror("Serial Connection Error", f"Error connecting to serial port: {e}")
        self.refresh_status

    def refresh_status(self):
        """Refresh the status display with the latest information."""
        print("Refreshing...")
        self.refresh_button.config(state='disabled', disabledforeground=self.refresh_button["foreground"])
        with self.serial_lock:
            self.update_transmit_power()
            self.update_tuning_status()
            self.update_active_vfo()
            self.update_frequency()
        self.refresh_button.config(state='normal')

    def refresh_status_periodically(self):
        """Periodically refresh the status every 15 seconds."""
        while True:
            time.sleep(1)
            self.refresh_status()

    def update_transmit_power(self):
        print("\tUpdate transmitpower")
        """Get the transmit power and update the status display."""
        if self.ser:
            self.ser.write(b"PC;")
            #response = self.ser.readline().decode().strip()
            response = self.ser.read_until(';').decode().strip()
            print(f'\t\t{response}')
            if response.startswith("PC"):
                power = response[2:-1]  # Remove "PC" and ";"
                self.transmit_power_value.config(text=f"{int(power)}w")  # Remove leading zeros and append "w"
            else:
                print(f"Invalid transmit power response: {response}")

    def update_tuning_status(self):
        print("\tUpdate tuningstatus")
        """Get the antenna tuner status and update the status display."""
        if self.ser:
            self.ser.write(b"AC;")
            response = self.ser.read_until(';').decode().strip()
            if response == "AC000;":
                self.tuning_status_value.config(text="Tune Off")
            elif response == "AC001;":
                self.tuning_status_value.config(text="Tune On")
            else:
                print(f"Invalid tuning status response: {response}")

    def update_active_vfo(self):
        print("\tUpdate vfo")
        """Get the active VFO and update the status display."""
        if self.ser:
            self.ser.write(b"VS;")
            response = self.ser.read_until(';').decode().strip()
            if response == "VS0;":
                self.active_vfo_value.config(text="VFO-A")
            elif response == "VS1;":
                self.active_vfo_value.config(text="VFO-B")
            else:
                print(f"Invalid VFO response: {response}")

    def update_frequency(self):
        print("\tUpdate freq")
        """Get the frequency of the active VFO and update the status display."""
        if self.ser:
            if self.active_vfo_value.cget("text") == "VFO-A":
                self.ser.write(b"FA;")
            elif self.active_vfo_value.cget("text") == "VFO-B":
                self.ser.write(b"FB;")
            response = self.ser.readline().decode().strip()
            try:
                frequency = float(response[2:-1])  # Remove "FA" or "FB" and ";"
                frequency = f"{frequency / 1000000:.6f}"  # Convert to MHz
                self.frequency_value.config(text=f"{frequency} MHz")
            except ValueError:
                print(f"Invalid frequency response: {response}")

    def tune(self):
        """Send the tune command to the transceiver."""
        if self.ser:
            self.ser.write(b"AC003;")
            response = self.ser.read_until(';').decode().strip()
            print(response)
            if response == "AC003;":
                print("Tune command sent.")
            else:
                print(f"Error sending tune command: {response}")
                input("enter to continue")

    def set_transmit_power(self):
        """Set the transmit power based on the user input."""
        power = self.transmit_power_input.get()
        if power.isdigit():
            power = int(power)
            if self.ser:
                self.ser.write(f"PC{power:03d};".encode())
                print(f"Transmit power set to {power}w")
        else:
            print("Invalid transmit power input")

    def power_on(self):
        """Turn on the power."""
        if self.ser:
            self.ser.write(b"PS1;")
            print("Power On command sent.")

    def power_off(self):
        """Turn off the power."""
        if self.ser:
            self.ser.write(b"PS0;")
            print("Power Off command sent.")

# Initialize the Tkinter application
root = tk.Tk()
app = SerialConnectionApp(root)
root.mainloop()
