#ifndef MICROPY_HW_BOARD_NAME
// Can be set by mpconfigboard.cmake.
#define MICROPY_HW_BOARD_NAME               "Waveshare ESP32-S3-Touch-LCD-1.47 LVGL"
#endif
#define MICROPY_HW_MCU_NAME                 "ESP32-S3R8"

// REPL tambien por UART0 (TX=43, RX=44, header), ademas del USB nativo. make.py ignora enable_uart_repl del .toml con --custom-board-path.
#define MICROPY_HW_ENABLE_UART_REPL         (1)

// Pila de la tarea de MicroPython: 32 KB (por defecto 16 KB). LVGL dibuja dentro de esta tarea (LV_OS_NONE, via TaskHandler) y con
// 16 KB se vio "stack overflow in task mp_thread". make.py ignora --task-stack-size con --custom-board-path; mpconfigport.h respeta este define.
#define MICROPY_TASK_STACK_SIZE             (32 * 1024)

// I2C0 -> touch AXS5106L (0x63). Sin IMU en esta placa.
#define MICROPY_HW_I2C0_SCL                 (41)
#define MICROPY_HW_I2C0_SDA                 (42)
