import sqlite3
import os
import sys
import pandas as pd

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

def stop_working(project_name):
    db_path = f'asdk_time_tracker.db'
    activities = input("What did you do in this session? ")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('''UPDATE project_time_tracking 
                      SET end_time = datetime('now'), activities = ? 
                      WHERE id = (SELECT MAX(id) FROM project_time_tracking)''', (activities,))
    connection.commit()
    connection.close()
    print(f"Stopped working on the project: {project_name} and recorded activities.")

def write_project_csv(project_name : str) -> None:
    db_path = f'{proj_name}.db'
    db = sqlite3.connect(db_path)
    # Query to list all tables
    query = "SELECT * FROM project_time_tracking;"
    res = db.execute(query).fetchall()

    print(res)
    df = pd.read_sql_query(query, db)
    if df.empty:
        print("No tables found in the database.")
    else:
        print("Tables in the database:")
        print(df)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        proj_name = input("Please provide a project name: ")
        start_working("asdk")
    else:
        project_name = sys.argv[1]
        start_working("asdk")