import os
import logging
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv(".env")

logging.basicConfig(level=os.getenv("LH_LOG_LEVEL", "DEBUG"))
