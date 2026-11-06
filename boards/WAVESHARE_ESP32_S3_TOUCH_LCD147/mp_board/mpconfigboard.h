#define MICROPY_HW_BOARD_NAME           "Waveshare ESP32-S3-Touch-LCD-1.47"
#define MICROPY_HW_MCU_NAME             "ESP32-S3R8"

// UART0 REPL on TX=43 RX=44 (header) and native USB CDC.
// Flash over native USB: hold BOOT, press RESET, release BOOT (no auto-reset).
#define MICROPY_HW_ENABLE_UART_REPL     (1)

// Pins confirmed with the official schematic (ESP32-S3-Touch-LCD-1.47-Schematic.pdf). Touch = AXS5106L (0x63). No IMU on board.
// I2C0 -> touch controller (TP_SDA=42, TP_SCL=41); also exposed on the header.
// Touch TP_RST=47, TP_INT=48.
#define MICROPY_HW_I2C0_SCL             (41)
#define MICROPY_HW_I2C0_SDA             (42)

// SPI1 -> ST7789 LCD 172x320 (x_offset=34). No MISO.
// LCD_CS=21, LCD_DC=45, LCD_RST=40, LCD_BL=46 (PWM)
#define MICROPY_HW_SPI1_SCK             (38)
#define MICROPY_HW_SPI1_MOSI            (39)
#define MICROPY_HW_SPI1_MISO            (-1)

// SDMMC -> TF card: machine.SDCard(slot=1, ...)
#define MICROPY_HW_SDMMC_CLK            (16)
#define MICROPY_HW_SDMMC_CMD            (15)
#define MICROPY_HW_SDMMC_D0             (17)
#define MICROPY_HW_SDMMC_D1             (18)
#define MICROPY_HW_SDMMC_D2             (13)
#define MICROPY_HW_SDMMC_D3             (14)

// BOOT button: GPIO0. Battery: BAT_ADC = GPIO12 (200K/100K divider, V = Vadc x 3)
