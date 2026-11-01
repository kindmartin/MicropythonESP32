#ifndef MICROPY_HW_BOARD_NAME
// Can be set by mpconfigboard.cmake.
#define MICROPY_HW_BOARD_NAME               "Waveshare ESP32-S3-Touch-LCD-2 LVGL"
#endif
#define MICROPY_HW_MCU_NAME                 "ESP32-S3R8"

// I2C0 -> CST816D touch (0x15) + QMI8658 IMU (0x6B)
#define MICROPY_HW_I2C0_SCL                 (47)
#define MICROPY_HW_I2C0_SDA                 (48)
