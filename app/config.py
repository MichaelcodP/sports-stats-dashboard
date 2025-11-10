from dotenv import load_dotenv
import os

load_dotenv()

THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")