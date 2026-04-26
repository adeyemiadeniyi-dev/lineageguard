import os
from dotenv import load_dotenv

load_dotenv()

OMD_URL = os.getenv("OMD_URL")
OMD_TOKEN = os.getenv("OMD_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")