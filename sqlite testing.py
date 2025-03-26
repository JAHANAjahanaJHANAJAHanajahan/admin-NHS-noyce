import sqlite3

patients = [
    ("Misha", "N6 4JS", "1949-06-10", "375634"),
    ("Tomo", "N3 3HS", "2001-10-13", "746837"),
    ("Isaac", "N4 2HA", "2008-04-28", "987123")
]

covid_vaccine = [
    ("375634", True, "Blue", "2025-03-11"),
    ("746837", True, "Green", "2025-03-11"),
    ("987123", True, None, None)
]

#connect to existing database or create new one
test = sqlite3.connect('example.sqlite')

#sql cursor creation
cursor = test.cursor()

cursor.execute('''
SELECT * FROM patient WHERE patient_name = ?
;
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS patients(name, postcode, dob, nin);
''')

cursor.execute('''INSERT INTO vaccination (patient_id, vaccine_type, date_administered) 
VALUES (?, ?, ?);
''')

cursor.execute('''
DROP TABLE IF EXISTS covid_vaccine;
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS covid_vaccine(nin, vaccine_type, date_administered);
''')
cursor.executemany('''
INSERT INTO covid_vaccine VALUES (?, ?, ?, ?);
''', covid_vaccine)

test.commit()
test.close()

