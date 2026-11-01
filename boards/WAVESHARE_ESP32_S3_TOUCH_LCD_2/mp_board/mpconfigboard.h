#define MICROPY_HW_BOARD_NAME           "Waveshare ESP32-S3-Touch-LCD-2"
#define MICROPY_HW_MCU_NAME             "ESP32-S3R8"

// UART0 REPL on TX=43 RX=44
#define MICROPY_HW_ENABLE_UART_REPL     (1)

// I2C0 -> CST816D touch (0x15) + QMI8658 IMU (0x6B)
#define MICROPY_HW_I2C0_SCL             (47)
#define MICROPY_HW_I2C0_SDA             (48)

// SPI1 (SPI2_HOST), shared by ST7789T3 LCD (CS=45, DC=42, BL=1, RST=none)
// and microSD in SPI mode (CS=41)
#define MICROPY_HW_SPI1_SCK             (39)
#define MICROPY_HW_SPI1_MOSI            (38)
#define MICROPY_HW_SPI1_MISO            (40)

// Battery voltage: GPIO5 (ADC1_CH4), 1/3 divider
// Camera (OV2640/OV5640, 24-pin DVP) for micropython-camera-API (USER_C_MODULES)
#define MICROPY_CAMERA_PIN_D0       (12)
#define MICROPY_CAMERA_PIN_D1       (13)
#define MICROPY_CAMERA_PIN_D2       (15)
#define MICROPY_CAMERA_PIN_D3       (11)
#define MICROPY_CAMERA_PIN_D4       (14)
#define MICROPY_CAMERA_PIN_D5       (10)
#define MICROPY_CAMERA_PIN_D6       (7)
#define MICROPY_CAMERA_PIN_D7       (2)
#define MICROPY_CAMERA_PIN_PCLK     (9)
#define MICROPY_CAMERA_PIN_VSYNC    (6)
#define MICROPY_CAMERA_PIN_HREF     (4)
#define MICROPY_CAMERA_PIN_XCLK     (8)
#define MICROPY_CAMERA_PIN_PWDN     (17)
#define MICROPY_CAMERA_PIN_RESET    (-1)
#define MICROPY_CAMERA_PIN_SIOD     (21)
#define MICROPY_CAMERA_PIN_SIOC     (16)
#define MICROPY_CAMERA_XCLK_FREQ    (20000000)
#define MICROPY_CAMERA_FB_COUNT     (2)
#define MICROPY_CAMERA_JPEG_QUALITY (85)
#define MICROPY_CAMERA_GRAB_MODE    (1)
