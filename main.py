"""
Main application script for MicroPython ESP32
Manages async tasks for button handling and display updates
"""
import asyncio
from page_btn import page_btn
from display import task_display


async def main_async():
    """
    Main async function that creates and manages concurrent tasks.
    Runs indefinitely in the background.
    """
    print("Starting main_async...")
    
    # Create concurrent tasks
    # NOTE: Tasks are intentionally not stored or awaited - they run indefinitely in background
    # This is the fire-and-forget pattern recommended for long-running background tasks
    asyncio.create_task(page_btn.task())
    asyncio.create_task(task_display())
    
    print("Tasks created, entering main loop")
    
    # Keep the main loop running
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour
