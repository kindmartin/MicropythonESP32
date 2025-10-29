# MicroPython ESP32 Modular Architecture

This project implements a modular architecture for MicroPython on ESP32, featuring background task execution with asyncio and threading support.

## Architecture Overview

The system uses a modular design with the following components:

### Core Files

#### `boot.py`
- Bootstrap script that runs automatically on MicroPython startup
- Starts the main application in a background thread (if threading is available)
- Falls back to main thread execution if threading fails
- Sets appropriate thread stack size (14KB) for ESP32

#### `main.py`
- Contains the main async event loop (`main_async()`)
- Creates and manages concurrent tasks for button handling and display updates
- Runs indefinitely in the background with a 1-hour sleep cycle

#### `page_btn.py`
- Button handling module
- Provides `page_btn` singleton instance with async `task()` method
- Monitors button state and handles press/release events
- Ready for integration with GPIO pins

#### `display.py`
- Display management module
- Provides `task_display()` async function for continuous display updates
- Includes utility functions for display operations (`show_message()`, `clear_display()`)
- Ready for integration with LCD/OLED displays

## How It Works

1. **Startup**: When ESP32 boots, MicroPython automatically runs `boot.py`
2. **Threading**: The `boot()` function attempts to start `main_async()` in a background thread
3. **Task Creation**: `main_async()` creates two concurrent tasks:
   - `page_btn.task()` - Handles button interactions
   - `task_display()` - Manages display updates
4. **Execution**: Both tasks run concurrently using asyncio, allowing responsive UI and background processing

## Code Flow

```python
boot.py
  └─> boot()
       ├─> _thread.start_new_thread() [if available]
       │    └─> asyncio.run(main_async())
       │         ├─> asyncio.create_task(page_btn.task())
       │         └─> asyncio.create_task(task_display())
       │
       └─> [fallback] asyncio.run(main_async())
```

## Threading Support

The architecture supports two execution modes:

1. **Background Thread Mode** (preferred):
   - Uses `_thread` module to run async tasks in background
   - Keeps REPL responsive for debugging
   - Stack size: 14KB (configurable)

2. **Main Thread Mode** (fallback):
   - Runs tasks in main thread if threading unavailable
   - Automatic fallback on threading errors

## Customization

### Adding New Tasks

To add a new async task, modify `main.py`:

```python
async def main_async():
    asyncio.create_task(page_btn.task())
    asyncio.create_task(task_display())
    asyncio.create_task(your_new_task())  # Add here
    
    while True:
        await asyncio.sleep(3600)
```

### Configuring Thread Stack Size

Edit `boot.py` to change stack size:

```python
_thread.stack_size(14 * 1024)  # Change multiplier as needed
```

### Task Update Intervals

- Button task: 1 second (in `page_btn.py`)
- Display task: 2 seconds (in `display.py`)
- Main loop: 3600 seconds / 1 hour (in `main.py`)

## Testing

Run the test suite to verify the architecture:

```bash
python3 test_architecture.py
```

The test suite validates:
- Module imports
- Async function structures
- Task execution
- Boot logic

## Hardware Integration

To integrate with actual hardware:

1. **Buttons** (`page_btn.py`):
   - Import `machine` module
   - Configure GPIO pins
   - Implement interrupt handlers in `_check_button_state()`

2. **Display** (`display.py`):
   - Import appropriate display driver (SSD1306, ILI9341, etc.)
   - Initialize display in module
   - Implement actual display updates in `_update_display()`

## Example Hardware Integration

```python
# page_btn.py - GPIO button example
from machine import Pin

class PageButton:
    def __init__(self):
        self.button = Pin(0, Pin.IN, Pin.PULL_UP)
        self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.handle_press)
    
    # ... rest of implementation

# display.py - SSD1306 OLED example
from machine import I2C, Pin
import ssd1306

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

async def task_display():
    while True:
        display.fill(0)
        display.text('Hello ESP32', 0, 0)
        display.show()
        await asyncio.sleep(2)
```

## Requirements

- MicroPython firmware for ESP32
- Asyncio support (included in modern MicroPython)
- Optional: _thread module for background execution

## Notes

- The main loop sleeps for 1 hour between iterations to conserve power
- All tasks run concurrently and independently
- Error handling ensures the system continues even if threading fails
- The architecture is extensible and modular for easy customization
