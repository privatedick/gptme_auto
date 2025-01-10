#!/usr/bin/env python3
from pathlib import Path
import asyncio
from src.task_queue import TaskQueue, initialize_queue

async def main():
    queue_file = Path("task_queue.json")
    # Initiera kön om den inte redan finns
    if not queue_file.exists():
        initialize_queue(queue_file)
    
    # Skapa och starta kön som bakgrundsprocess
    queue = TaskQueue(queue_file, max_parallel=3)
    await queue.run_queue()

if __name__ == "__main__":
    asyncio.run(main())
