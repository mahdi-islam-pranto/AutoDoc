from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from utilities.helper import get_db_uri, get_async_connection_pool

# module-level singleton
_checkpointer = None  

async def get_checkpointer():
    """Returns a singleton AsyncPostgresSaver instance."""
    global _checkpointer
    if _checkpointer is None:
        print("Initializing AsyncPostgresSaver...")

        pool = get_async_connection_pool(get_db_uri, 10, {"autocommit": True, "prepare_threshold": 0}, False)
        
        # Open the connection pool before using it
        await pool.open()
        
        _checkpointer = AsyncPostgresSaver(conn=pool)
        await _checkpointer.setup()  # creates checkpointer tables if they don't exist
        
        print("AsyncPostgresSaver initialized and connected to DB.")
    return _checkpointer