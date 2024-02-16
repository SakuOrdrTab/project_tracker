import sqlite3
import pandas as pd

if __name__ == "__main__":
    project = input("What is the name of the project: ")
    db_path = f'asdk_time_tracker.db'
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
