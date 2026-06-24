import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to get PostgreSQL database configuration from environment variables
def get_postgresql_db_config():
    postgresql_config = {
        "host": os.getenv("P_DB_HOST", "default_localhost"),
        "port": os.getenv("P_DB_PORT"),
        "database": os.getenv("P_DB_NAME"),
        "user": os.getenv("P_DB_USER"),
        "password": os.getenv("P_DB_PASSWORD")
    }

    return postgresql_config
