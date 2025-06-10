import asyncio
from pathlib import Path
import sys

# Add src to path for clean imports
sys.path.append(str(Path(__file__).parent / "src"))

from database.supabase_client import SupabaseClient
from loguru import logger

async def clear_broadcast_logs():
    """Connects to Supabase and deletes all entries from the broadcast_logs table."""
    logger.info("Attempting to clear the 'broadcast_logs' table in Supabase...")
    
    try:
        supabase_client = SupabaseClient().client
        if not supabase_client:
            logger.error("Failed to initialize Supabase client.")
            return

        logger.warning("This will delete all records from 'broadcast_logs'.")
        
        # Step 1: Fetch all record IDs from the table.
        select_response = await supabase_client.table('broadcast_logs').select('id').execute()
        
        if not select_response.data:
            logger.info("Table 'broadcast_logs' is already empty.")
            return

        record_ids = [record['id'] for record in select_response.data]
        logger.info(f"Found {len(record_ids)} records to delete.")

        # Step 2: Delete the records using the fetched IDs.
        if record_ids:
            delete_response = await supabase_client.table('broadcast_logs').delete().in_('id', record_ids).execute()

            if delete_response.data:
                logger.success(f"Successfully deleted {len(delete_response.data)} records from 'broadcast_logs'.")
            else:
                logger.error("Delete operation failed or returned no data.")
                if hasattr(delete_response, 'error') and delete_response.error:
                    logger.error(f"Supabase API error: {delete_response.error.message}")
        else:
            logger.info("No records to delete.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(clear_broadcast_logs()) 