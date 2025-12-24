![Cross-Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-0078D4?style=for-the-badge&logo=windows&logoColor=white)

# A Small project time tracker

## Install

This project tracker works on Windows, Linux, macOS, and other Unix-like systems. Pick a nice folder where you're comfortable placing the project root, as you'll want a centralized location to track multiple projects.

Clone the repo there, create a virtual environment named `.venv` and install requirements:

### Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS/Unix

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Setting up PATH

Add the project root to your system PATH:

**Windows:** Add the project root to your system PATH so that Windows can find the `proj_ttrack.cmd` script from anywhere.

**Linux/macOS/Unix:** Add the project root to your PATH and ensure `proj_ttrack.sh` has execute permissions (it should by default). You can add this line to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="/path/to/project_tracker:$PATH"
```

<b>NOTICE:</b>
The default database is currently the Supabase PostgreSQL database in the cloud; this you can track projects from your all devices in contrast to a local file database, that of course tracks only the operated computer/device.

To be able to use the Supabase, you must of course create a (free) account there and obtain passwords, username, url etc. The `PostgreCloudStorage` class loads these variables from the environment. Set a `.env` file on accordance to the `.env.example`:
```
POSTGRES_URL=
TEST_POSTGRES_URL=
```

I strongly encourage to create a different project in Supabase for testing, if you want to try the tests. Currently the test skip Supabase/Postgres tests, if no TEST_POSTGRES_URL is provided.

<b>WARNING:</b> If you set your production POSTGRES_URL to TEST_POSTGRES_URL, the <b> tests will erase your production database when run!</b>

To use Supabase ipV4 compliant <i>Session pooler</i> database, the POSTGRES_URL is in the style:<br>
`postgresql://{username}:{password}@{host}:{port}/{database}`


## Usage

This script is designed to be used from a command prompt/terminal. After you have added the project root to your PATH, run:

**Windows:**
```cmd
proj_ttrack <args>
```

**Linux/macOS/Unix:**
```bash
proj_ttrack.sh <args>
```

<I>'<project_name> --start'</I> Sets a starting time for a project work session. Run this when you start coding<BR>
<I>'<project_name> --stop <optional_text>'</I>  Sets the closing time, use when you stop coding. if optional text is empty, it asks for what you did during the session<BR>
<I>'<project_name> --export'</I> exports your sessions to a `.csv`-file<BR>
<I>'<project_name> --print'</I> Prints your sessions in a project<BR>
<I>'--list'</I> Lists all tracked projects in database<BR>
<I>'--install'</I> Installs two script files to your current working directory:
- On Windows: `start_track.bat` and `stop_track.bat`
- On Linux/macOS/Unix: `start_track.sh` and `stop_track.sh`

I suggest running `--install` in each project directory where you want to track time sessions. These scripts make it easier by not requiring you to type the project name every time.<BR>

After installing the script files to a project directory, you can start and stop time tracking for that project:

**Windows:**
```cmd
start_track
stop_track <optional text>
```

**Linux/macOS/Unix:**
```bash
./start_track.sh
./stop_track.sh <optional text>
```

Remember, these scripts only work for starting and stopping sessions. If you want to e.g. export the sessions, you have to use `proj_ttrack` (or `proj_ttrack.sh`):

**Windows:**
```cmd
proj_ttrack <project> --export
```

**Linux/macOS/Unix:**
```bash
proj_ttrack.sh <project> --export
```

## GitHub actions

I set up a workflow to run the local tests every 6 days, as Supabase puts databases to sleep after 7 days in the free tier. This is especially a problem for the test DB, as it can be a while between running the tests. The action wakes up the Supabase DBs, so you don't have to worry about that.

I don't know if you clone/fork the repo if the actions are on by default or do you need to turn them on manually.

Anyhow, if you want to use the tests, you must set up the Supabase DB uris as GitHub actions secrets. See the secret names in the `.env.example`.


## Additional info

The program uses currently supabase and PostgreSQL for managing data.

Currently, the program logic prevents non-sequential "starts" and "stops". By that I mean, if you forget to close a session, it becomes impossible to alter the closing time for example the next day you happen to notice it. Also, if you "add just a few lines of code more", you can't put another stop mark to the session. However, if you want program to work differently in these regards, feel free just altering a bit the `.start_working()` and `.stop_working()` methods, they can handle nulls etc quite easily without overt recoding. And if you are using Supabase or other external DB, you can edit the data there.
