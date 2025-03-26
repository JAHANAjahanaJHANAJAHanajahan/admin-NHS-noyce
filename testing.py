import tkinter as tk
import random

# Expanded list of sample names
sample_names = [
    "John Smith", "Jane Doe", "Alice Johnson", "Bob Brown", "Charlie White",
    "Emily Davis", "Michael Green", "Olivia Black", "Ethan Miller", "Sophia Wilson",
    "Liam Turner", "Emma Watson", "Noah Clarke", "Ava Scott", "Oliver Lewis",
    "Isabella King", "Elijah Walker", "Mia Young", "William Hill", "Charlotte Adams",
    "James Carter", "Amelia Mitchell", "Benjamin Phillips", "Harper Campbell", "Lucas Roberts"
]

# Global variables to store current patient data
current_name = ""
current_age = 0
name_sequence = []  # This will hold the shuffled names sequence
name_index = 0      # Pointer to the current name in the sequence

def initialize_names():
    """Shuffles the names and resets the sequence."""
    global name_sequence, name_index
    name_sequence = sample_names.copy()
    random.shuffle(name_sequence)
    name_index = 0

def get_next_name():
    """Returns the next name from the shuffled sequence; re-shuffles if end is reached."""
    global name_index
    if name_index >= len(name_sequence):
        initialize_names()
    name = name_sequence[name_index]
    name_index += 1
    return name

def generate_patient():
    """Generates a new patient with the next name in sequence and a random age, then updates the display."""
    global current_name, current_age
    current_name = get_next_name()
    current_age = random.randint(0, 100)  # Random age between 0 and 100
    update_display()

def update_display():
    """Updates the patient display label with the current name and age."""
    patient_info = f"Name: {current_name}\nAge: {current_age}"
    # Left align the text using anchor and justify options.
    patient_label.config(text=patient_info, anchor="w", justify="left")

def increment_age():
    """Increments the current patient's age by 1 and updates the display."""
    global current_age
    current_age += 1
    update_display()

# Create the main window
root = tk.Tk()
root.title("Patient Simulator for System Test")
root.geometry("400x250")

# Label to display the patient information, fixed at a set location (using pack with anchor 'w')
patient_label = tk.Label(root, text="", font=("Arial", 24), anchor="w", justify="left")
patient_label.pack(pady=20, padx=20, fill="x")

# Frame to hold the buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Button to simulate the next patient
next_button = tk.Button(button_frame, text="Next Patient", font=("Arial", 16), command=generate_patient)
next_button.grid(row=0, column=0, padx=10)

# Button to increment the current patient's age by 1
increment_button = tk.Button(button_frame, text="Next Year", font=("Arial", 16), command=increment_age)
increment_button.grid(row=0, column=1, padx=10)

# Initialize the names sequence and generate the first patient on startup
initialize_names()
generate_patient()

# Run the application
root.mainloop()
