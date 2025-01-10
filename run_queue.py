#!/usr/bin/env python3
"""Queue runner script for AI-assisted development system.

This script initializes and runs the task queue system. It handles:
- Queue initialization
- Task processing
- Graceful shutdown
- Error handling and logging
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.task_queue import TaskQueue, initialize_queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('queue_runner.log')
    ]
)

logger = logging.getLogger("QueueRunner")

# Global queue reference for signal handling
queue: TaskQueue = None


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    if queue:
        logger.info("Shutdown signal received, stopping queue...")
        asyncio.create_task(queue.stop())
    else:
        logger.info("Shutdown signal received before queue initialization")
        sys.exit(0)


async def main():
    """Run the task queue system."""
    global queue
    
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Setup queue file path
        queue_file = Path("task_queue.json")
        
        # Initialize queue if it doesn't exist
        if not queue_file.exists():
            logger.info("Initializing new task queue")
            initialize_queue(queue_file)
        
        # Create and run queue
        queue = TaskQueue(queue_file, max_parallel=3)
        logger.info("Starting task queue processing")
        await queue.run_queue()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        if queue:
            logger.info("Stopping queue gracefully...")
            await queue.stop()
    except Exception as e:
        logger.error(f"Error running queue: {e}", exc_info=True)
        if queue:
            await queue.stop()
        raise
    finally:
        logger.info("Queue runner shutting down")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
