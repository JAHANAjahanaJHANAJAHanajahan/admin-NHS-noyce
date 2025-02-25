import sqlite3

#connect to existing database or create new one
test = sqlite3.connect('example.sqlite')

#sql cursor creation
cursor = test.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS patient (
ID INTEGER PRIMARY KEY AUTOINCREMENT,
age REAL, 
name TEXT)
''')

cursor.execute('''INSERT INTO patient (Age, Name) VALUES ("65", "John")''')
test.commit()
test.close()

