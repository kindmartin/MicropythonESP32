"""
Boot script for MicroPython ESP32
Runs the main script in background using threading and asyncio
"""
import asyncio
try:
    import _thread
except ImportError:
    _thread = None


def boot():
    """
    Bootstrap function to start the main application.
    Attempts to run main_async in a separate thread if threading is available,
    otherwise runs it in the main thread.
    """
    from main import main_async
    
    try:
        if _thread:
            # Set thread stack size to 14KB for ESP32
            _thread.stack_size(14 * 1024)
            # Start main_async in a new thread
            _thread.start_new_thread(lambda: asyncio.run(main_async()), ())
            print("Main script started in background thread")
        else:
            # Fallback: run in main thread if threading not available
            print("Threading not available, running in main thread")
            asyncio.run(main_async())
    except Exception as e:
        # Fallback: run in main thread on error
        print(f"Error starting thread: {e}")
        print("Falling back to main thread execution")
        asyncio.run(main_async())


# Start the application
boot()
