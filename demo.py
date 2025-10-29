"""
Demo script to demonstrate the modular MicroPython architecture
Runs a short simulation of the boot process and task execution
"""
import asyncio
import sys
from unittest.mock import Mock

# Mock _thread for demonstration
_thread_mock = Mock()
sys.modules['_thread'] = _thread_mock

print("=" * 60)
print("MicroPython ESP32 Modular Architecture Demo")
print("=" * 60)

print("\n1. Simulating boot.py execution...")
print("-" * 60)

# Import after mocking
from main import main_async
from page_btn import page_btn
from display import task_display

print("\n2. Starting async tasks (limited to 10 seconds for demo)...")
print("-" * 60)

async def demo_main():
    """Demo version of main_async with shorter runtime"""
    print("\n[main_async] Creating tasks...")
    
    # Create tasks exactly as in the problem statement
    task1 = asyncio.create_task(page_btn.task())
    task2 = asyncio.create_task(task_display())
    
    print("[main_async] Tasks created, running for 10 seconds...\n")
    
    # Run for 10 seconds instead of forever (for demo purposes)
    await asyncio.sleep(10)
    
    print("\n[main_async] Demo complete, cancelling tasks...")
    task1.cancel()
    task2.cancel()
    
    try:
        await task1
    except asyncio.CancelledError:
        pass
    
    try:
        await task2
    except asyncio.CancelledError:
        pass

# Run the demo
asyncio.run(demo_main())

print("\n" + "=" * 60)
print("Demo completed successfully!")
print("=" * 60)

print("\n3. Architecture Summary:")
print("-" * 60)
print("✓ boot.py: Bootstrap script with threading support")
print("✓ main.py: Main async event loop with task management")
print("✓ page_btn.py: Button handling module with async task")
print("✓ display.py: Display management module with async task")
print("\n4. Key Features:")
print("-" * 60)
print("✓ Background execution using _thread (with fallback)")
print("✓ Concurrent tasks using asyncio")
print("✓ Modular architecture for easy extension")
print("✓ Proper error handling and fallback mechanisms")
print("✓ Configurable thread stack size (14KB for ESP32)")
print("\n" + "=" * 60)
