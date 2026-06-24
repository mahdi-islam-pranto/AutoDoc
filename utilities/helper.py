from config.db import get_postgresql_db_config
from psycopg_pool import AsyncConnectionPool

# get_db_uri() returns a URI string like:
# "postgresql://postgres:12345678@localhost:5432/ihelp_doctor_appointment"
def get_db_uri():
    db_config = get_postgresql_db_config()

    db_uri = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    return db_uri

# This function creates and returns an AsyncConnectionPool instance.
def get_async_connection_pool(get_db_uri, max_size=10, kwargs=None, open=False):
    if kwargs is None:
        kwargs = {"autocommit": True, "prepare_threshold": 0}

    # For async libraries like asyncpg, the URI format is the same as for sync libraries
    pool =  AsyncConnectionPool(
            conninfo=get_db_uri(),
            max_size=max_size,
            kwargs=kwargs,
            open=open  # we open it manually below
        )
    return pool

def generate_graph_config(channel, user_id, langfuse_handler=None):
    
    # Create a unique thread ID for this user (could be more complex in real app)
    thread_id = f"{channel}:{user_id}"
    return {
        "configurable": {
            "thread_id": thread_id,
        },
        "callbacks": langfuse_handler
    }