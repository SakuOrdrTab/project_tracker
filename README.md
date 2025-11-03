# A Small project time tracker

## Install

These instructions are made for usage in Windows platform; you need to make tweaks for the shell scripts etc for this to work in unix, linux and whatever... I also assume you want to have a centralized location for the script as you want to track multiple projects.

Pick a nice folder, that you are comfortable placing the project root later to system PATH. 
Clone the repo there, create a virtual environment named `.venv` and install requirements:

>python - m venv .venv
>
>.venv\Scripts\activate
>
>pip install -r requirements.txt
>

Add then the project root to your system PATH, so that your windows finds the proj_ttrack.cmd script from anywhere.

<b>NOTICE:</b>
The default database is currently the Supabase PostgreSQL database in the cloud; this you can track projects from your all devices in contrast to a local file database, that of course tracks only the operated computer/device.

To be able to use the Supabase, you must of course create a (free) account there and obtain passwords, username, url etc. The `PostgreCloudStorage` class loads these variables from the environment. Set a `.env` file on accordance to the `.env.example`:
```
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DBNAME=postgres
```

## Usage

This script is designed to be used from a command prompt. After you have added the project root to your PATH, just run:

>proj_ttrack <args>

<I>'<project_name> -start'</I> Sets a starting time for a project work session. Run this when you start coding<BR>
<I>'<project_name> -stop <optional_text>'</I>  Sets the closing time, use when you stop coding. if optional text is empty, it asks for what you did durring the session<BR>
<I>'<project_name> -export'</I> Prints your sessions to a `.csv`-file<BR>
<I>'-list'</I> Lists all tracked projects in database<BR>
<I>'-install'</I> Adds two windows batch files, start_track.bat and stop_track.bat to your current working directory. I suggest that as your proj_ttrack is in your PATH, you run this in your new project where you want to track time sessions. Running the bats eases you from typing the project name every time.<BR>

After installing the windows batch files to a project directory, you can just start and stop time tracking for that particular project with the bats:

>start_track

>stop_track <optional text>

Remember, these only work for starting and stopping the sessions. If youwant to e.g. export the sessions, you have to use `proj_ttrack`:

>proj_ttrack <project> -export


## Additional info

The program uses currently supabase and PostgreSQL for managing data.

Currently, the program logic prevents sequential "starts" and "stops". This means, that if you forget to close a session, it becomes impossible to alter the closing time for example the next day you happen to notice it. Also, if you "add just a few lines of code more", you can't put another stop mark to the session. However, if you want program to wrok differently in these regards, feel free just altering a bit the `.start_working()` and `.stop_working()` methods, they can handle nulls etc quite easily without overt recoding.
