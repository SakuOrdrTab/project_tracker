'''settings.py'''

# This script loads the environment variables to constants needed in the project.

import os
from dotenv import load_dotenv

load_dotenv()

TEST = os.environ.get("TEST")
