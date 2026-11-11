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
The tracker uses a Neon PostgreSQL database in the cloud so you can track projects from multiple devices. Other PostgreSQL providers also work through SQLAlchemy. I used to use Supabase, but it's policy of shutting down projects was FAR too annoying; unless I was actively developing, the test database was shut down and thus unavailable when needed. I can recommend the Neon, though..

Create a project in [Neon](https://neon.com), open **Connect**, and copy the connection URL. Change its scheme from `postgresql://` to `postgresql+psycopg://`, keeping the credentials, database name, and SSL parameters. Copy `.env.example` to `.env` and set:
```
POSTGRES_URL="postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require&channel_binding=require"
TEST_POSTGRES_URL=
```

`POSTGRES_URL` is used by the tracker. `TEST_POSTGRES_URL` is used only by the PostgreSQL integration tests. Environment variables already set in your shell take precedence over `.env`.

For tests, create a separate, disposable database named `project_tracker_test` in Neon. It can be in the same project; a separate project or branch is optional. Use a dedicated SQL-created login with access to the test schema and no write privileges on production tables. Roles created through the Neon Console have administrative privileges; see [Neon's database access guide](https://neon.com/docs/manage/database-access) for creating a limited role.

Set `TEST_POSTGRES_URL` to that database's URL using `postgresql+psycopg://` and the test login. The suite refuses database names that do not end in `_test`, and refuses a test URL matching the configured production endpoint and database.

**Warning:** PostgreSQL integration tests delete all rows in the test database's `project_sessions` table. Never use production credentials or a database containing data you need. Leave `TEST_POSTGRES_URL` empty to skip these tests.

Run the suite with:

```bash
python -m pytest
```

The application and tests use the Python driver; a local PostgreSQL server or command-line tools are not required. Install `pg_dump`, `pg_restore`, and `psql` separately when needed for backups or database administration.

Neon automatically wakes an idle compute on the next connection, so no keep-alive workflow is needed. Free-tier usage limits still apply; see [Neon's current plans](https://neon.com/docs/introduction/plans).

When moving an existing tracker database, changing the URL does not copy data. Back up and restore `project_sessions`, including its ID sequence, then compare the records before changing the production URL. Initialization creates missing tables but does not import existing sessions.


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

The `Tests` workflow in `.github/workflows/tests.yml` runs on pushes to `master` (including merges), pull requests targeting `master`, and manual dispatch. Pushes to other branches do not trigger it unless they update a pull request targeting `master`. It does not connect to production or run on a keep-alive schedule.

In GitHub **Settings → Secrets and variables → Actions**, create a repository secret named `TEST_POSTGRES_URL` using the dedicated Neon test URL from your local `.env`. The production `POSTGRES_URL` secret is not used and can be removed. Secrets are not passed to pull requests from forks, so PostgreSQL tests are skipped there and whenever the test URL is absent.

Commit and push the workflow change, and enable Actions if it is disabled. Never commit `.env` or paste connection strings into workflow files.


## Additional info

The program uses Neon PostgreSQL and SQLAlchemy for managing data.

Currently, the program logic prevents non-sequential "starts" and "stops". By that I mean, if you forget to close a session, it becomes impossible to alter the closing time for example the next day you happen to notice it. Also, if you "add just a few lines of code more", you can't put another stop mark to the session. However, if you want program to work differently in these regards, feel free just altering a bit the `.start_working()` and `.stop_working()` methods, they can handle nulls etc quite easily without overt recoding. You can also edit the data in the Neon SQL Editor.
