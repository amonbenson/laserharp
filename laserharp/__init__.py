import os
import logging
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local", override=True)

logging.basicConfig(level=os.getenv("LH_LOG_LEVEL", "DEBUG"))
