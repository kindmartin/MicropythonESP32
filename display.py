"""
Display module for handling display updates
Provides async task for display refresh and content updates
"""
import asyncio


async def task_display():
    """
    Async task for managing display updates.
    Runs continuously to refresh and update the display content.
    """
    print("Display task started")
    counter = 0
    
    while True:
        # Simulate display update logic
        # In a real implementation, this would update LCD/OLED display
        counter += 1
        if counter % 5 == 0:
            print(f"Display task running... (iteration {counter})")
        
        # Update display content
        # NOTE: Uncomment and implement _update_display() when integrating with actual hardware
        # await _update_display()
        
        await asyncio.sleep(2)  # Update every 2 seconds


async def _update_display():
    """
    Internal function to update display content.
    Override this in actual implementation to write to hardware.
    """
    # Placeholder for actual display update logic
    pass


def clear_display():
    """Clear the display"""
    print("Display cleared")


def show_message(message: str):
    """
    Display a message on the screen.
    
    Args:
        message: The message to display
    """
    print(f"Display: {message}")
