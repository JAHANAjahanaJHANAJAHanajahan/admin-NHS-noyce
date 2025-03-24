import sqlite3

# Creates a connection to the SQLite database (or creates it if it doesn't exist)
conn = sqlite3.connect('nhs_vaccination.db')
cursor = conn.cursor()

# Creates Patients table
cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
                    patient_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    email TEXT)''')

# Creates Vaccines table
cursor.execute('''CREATE TABLE IF NOT EXISTS vaccines (
                    vaccine_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    dose INTEGER NOT NULL)''')

# Creates Appointments table to link patients and vaccines
cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id INTEGER PRIMARY KEY,
                    patient_id INTEGER,
                    vaccine_id INTEGER,
                    appointment_date TEXT NOT NULL,
                    FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
                    FOREIGN KEY(vaccine_id) REFERENCES vaccines(vaccine_id))''')

# Inserts some sample data
cursor.execute('''INSERT INTO patients (name, age, email) 
                  VALUES ('John Doe', 45, 'john.doe@example.com')''')
cursor.execute('''INSERT INTO vaccines (name, dose) 
                  VALUES ('Pfizer', 1)''')

# Links a patient to a vaccine through an appointment
cursor.execute('''INSERT INTO appointments (patient_id, vaccine_id, appointment_date) 
                  VALUES (1, 1, '2025-04-01')''')

# Commits the changes and close the connection
conn.commit()

# Querys the tables to see the data
cursor.execute('''SELECT patients.name, vaccines.name, appointments.appointment_date 
                  FROM appointments 
                  JOIN patients ON appointments.patient_id = patients.patient_id 
                  JOIN vaccines ON appointments.vaccine_id = vaccines.vaccine_id''')

# Prints out the appointment information
for row in cursor.fetchall():
    print(f"Patient: {row[0]}, Vaccine: {row[1]}, Appointment Date: {row[2]}")

conn.close()

