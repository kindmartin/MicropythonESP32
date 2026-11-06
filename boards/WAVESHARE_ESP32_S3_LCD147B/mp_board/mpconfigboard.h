#define MICROPY_HW_BOARD_NAME           "Waveshare ESP32-S3-LCD-1.47B"
#define MICROPY_HW_MCU_NAME             "ESP32-S3R8"

// REPL on UART0 (TX=43, RX=44, exposed on the header) and also on native USB CDC.
// Flash over native USB: hold BOOT, press RESET, release BOOT (no auto-reset).
#define MICROPY_HW_ENABLE_UART_REPL     (1)

// Pins from waveshare.com/wiki/ESP32-S3-LCD-1.47B and the official schematic.
// I2C0 -> QMI8658 IMU (0x6B); IMU_INT1=GPIO13, IMU_INT2=GPIO12
#define MICROPY_HW_I2C0_SCL             (47)
#define MICROPY_HW_I2C0_SDA             (48)

// Battery voltage: GPIO1 (BAT_ADC), divider 200K/100K -> V = Vadc x 3
// BOOT button: GPIO0

// SPI1 -> ST7789 LCD 172x320 (x_offset=34). No MISO.
// CS=42, DC=41, RST=39, BL=46 (PWM)
#define MICROPY_HW_SPI1_SCK             (40)
#define MICROPY_HW_SPI1_MOSI            (45)
#define MICROPY_HW_SPI1_MISO            (-1)

// WS2812 RGB LED data: GPIO38

// SDMMC -> TF card (1-bit/4-bit): use machine.SDCard(slot=1, ...)
#define MICROPY_HW_SDMMC_CLK            (14)
#define MICROPY_HW_SDMMC_CMD            (15)
#define MICROPY_HW_SDMMC_D0             (16)
#define MICROPY_HW_SDMMC_D1             (18)
#define MICROPY_HW_SDMMC_D2             (17)
#define MICROPY_HW_SDMMC_D3             (21)
