"""
Test script to verify the modular MicroPython architecture
Simulates the boot process and verifies async tasks run correctly
"""
import asyncio
import sys
import time
from unittest.mock import Mock, patch

# Mock _thread module if not available
try:
    import _thread
except ImportError:
    _thread = Mock()
    _thread.stack_size = Mock()
    _thread.start_new_thread = Mock(side_effect=lambda func, args: func())
    sys.modules['_thread'] = _thread


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        import main
        import page_btn
        import display
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_page_btn_module():
    """Test page_btn module functionality"""
    print("\nTesting page_btn module...")
    try:
        from page_btn import page_btn
        assert hasattr(page_btn, 'task'), "page_btn should have task method"
        assert asyncio.iscoroutinefunction(page_btn.task), "task should be async"
        print("✓ page_btn module structure is correct")
        return True
    except Exception as e:
        print(f"✗ page_btn test failed: {e}")
        return False


def test_display_module():
    """Test display module functionality"""
    print("\nTesting display module...")
    try:
        from display import task_display, show_message, clear_display
        assert asyncio.iscoroutinefunction(task_display), "task_display should be async"
        assert callable(show_message), "show_message should be callable"
        assert callable(clear_display), "clear_display should be callable"
        print("✓ display module structure is correct")
        return True
    except Exception as e:
        print(f"✗ display test failed: {e}")
        return False


def test_main_module():
    """Test main module functionality"""
    print("\nTesting main module...")
    try:
        from main import main_async
        assert asyncio.iscoroutinefunction(main_async), "main_async should be async"
        print("✓ main module structure is correct")
        return True
    except Exception as e:
        print(f"✗ main test failed: {e}")
        return False


async def test_async_execution():
    """Test that async tasks can run"""
    print("\nTesting async execution...")
    try:
        from page_btn import page_btn
        from display import task_display
        
        # Create tasks
        task1 = asyncio.create_task(page_btn.task())
        task2 = asyncio.create_task(task_display())
        
        # Let them run briefly
        await asyncio.sleep(3)
        
        # Cancel tasks
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
        
        print("✓ Async tasks executed successfully")
        return True
    except Exception as e:
        print(f"✗ Async execution test failed: {e}")
        return False


def test_boot_logic():
    """Test boot module logic"""
    print("\nTesting boot module logic...")
    try:
        # We won't actually run boot since it starts infinite loops
        # Just verify the structure
        with open('boot.py', 'r') as f:
            content = f.read()
            assert 'def boot()' in content, "boot() function should exist"
            assert 'main_async' in content, "should import main_async"
            assert '_thread.stack_size' in content, "should set thread stack size"
            assert 'asyncio.run' in content, "should use asyncio.run"
        print("✓ boot module structure is correct")
        return True
    except Exception as e:
        print(f"✗ boot test failed: {e}")
        return False


def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("MicroPython Modular Architecture Tests")
    print("=" * 50)
    
    results = []
    results.append(test_imports())
    results.append(test_page_btn_module())
    results.append(test_display_module())
    results.append(test_main_module())
    results.append(asyncio.run(test_async_execution()))
    results.append(test_boot_logic())
    
    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 50)
    
    return all(results)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
