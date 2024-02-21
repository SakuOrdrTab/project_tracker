# A Small project time tracker

## Install
This is a python script.

To install, clone it to a suitable folder for python projects, let's say C:\PYTHON\project_tracker

Then, create a virtual environment for the project, activate it and install dependancies

>python - m venv .venv
>
>.venv\Scripts\activate
>
>pip install -r requirements.txt
>

Then you can run it with your python interpreter

>python proj_ttracker.py
>

## Usage

This script is designed to be used from a command prompt:

>python proj_ttracker.py <project_name> -start/-stop/-print <optional_args>
>

<I>'<project_name> -start'</I> Sets a starting time for a project work session. Run this when you start coding<BR>
<I>'<project_name> -stop <optional_text>'</I>  Sets the closing time, use when you stop coding. if optional text is empty, it asks for what you did durring the session<BR>
<I>'-print'</I> Prints your sessions to a `.csv`-file<BR>

I find it easiest, that if I start a project, I create two windows thumbnails with different args; one for starting to code the project, another to quit a session. When I work a session with the project, I run the first thumbnail, then when I finish, I run the latter. An example in windows for a suitable batch file could be like this:
>`start.bat`<BR>
>cd C:\Users\user\Documents\Python\project_tracker<BR>
><BR>
>:: activate virtual env, call is necessary because of path env var update<BR>
>call .\.venv\Scripts\activate<BR>
><BR>
>:: run the venv version python.exe<BR>
>python.exe .\proj_ttrack.py .\koikka -start<BR>
>.\.venv\Scripts\deactivate<BR>

## Additional info

The program uses SQLite for managing data.

Currently, the program logic prevents sequential "starts" and "stops". This means, that if you forget to close a session, it becomes impossible to alter the closing time for example the next day you happen to notice it. Also, if you "add just a few lines of code more", you can't put another stop mark to the session. However, if you want program to wrok differently in these regards, feel free just altering a bit the `.start_working()` and `.stop_working()` methods, they can handle nulls etc quite easily without overt recoding.
