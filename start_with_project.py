import sqlite3
import os
import sys

def initialize_database(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS project_time_tracking 
                    (id INTEGER PRIMARY KEY, start_time TEXT, end_time TEXT, activities TEXT)''')
    connection.commit()
    connection.close()

def start_working(project_name):
    db_path = f'.\{project_name}_time_tracker.db'
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO project_time_tracking (start_time) VALUES (datetime('now'))")
    connection.commit()
    connection.close()
    print(f"Started working on the project: {project_name}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        proj_name = input("Please provide a project name: ")
        start_working("asdk")
    else:
        project_name = sys.argv[1]
        start_working("asdk")