import sqlite3
import sys

def stop_working(project_name):
    db_path = f'c:/python/{project_name}_time_tracker.db'
    activities = input("What did you do in this session? ")
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('''UPDATE project_time_tracking 
                      SET end_time = datetime('now'), activities = ? 
                      WHERE id = (SELECT MAX(id) FROM project_time_tracking)''', (activities,))
    connection.commit()
    connection.close()
    print(f"Stopped working on the project: {project_name} and recorded activities.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a project name.")
    else:
        project_name = sys.argv[1]
        stop_working(project_name)