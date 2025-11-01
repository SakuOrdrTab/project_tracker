"""Installer for Windows batch files. Installer adds to current working directory two .bat files, 
start_track and stop_track that don't need any arguments and allow quick session management in 
each project"""

from os import path, getcwd

# Illegal windows filename chars
ILLEGAL_CHARS = set('<>:"/\\|?*')

def validate_proj_name(name: str) -> bool:
    # Check for empty string and path manipulation attempts
    if not name or path.normpath(name) != name:
        return False
        
    if any(c.isspace() for c in name):
        return False
        
    if any(char in name for char in ILLEGAL_CHARS):
        return False
        
    return True


def install_bats_to_cwd() -> None:
    print("Installer running...")

    # Make sure that it is the CWD
    cwd = getcwd()
    start_path = path.join(cwd, 'start_track.bat')
    stop_path = path.join(cwd, 'stop_track.bat')

    proj_name = input("What is the name of your project: ")
    while True:
        if validate_proj_name(proj_name):
            break
        print("""Project name has to compatible with Windows filenames in order to use  windows bats for
running the sessions. No whitespacesor certain special characters.
for 'my funny project' you can use 'my-funny-project' for example""")
        proj_name = input("Please give a new name: ")

    start_bat = f'''
    proj_ttrack {proj_name} -start
    '''

    stop_bat = f'''
    proj_ttrack {proj_name} -stop %*
    '''

    with open(start_path, "w", encoding="utf-8") as file:
        file.writelines(start_bat)

    with open(stop_path, "w", encoding="utf-8") as file:
        file.writelines(stop_bat)
    
    return None
    