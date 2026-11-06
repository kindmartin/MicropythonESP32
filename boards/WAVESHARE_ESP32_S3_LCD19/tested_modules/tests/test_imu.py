# IMU QMI8658 (I2C SDA47 SCL48, 0x6B): inclina/agita la placa. En reposo |a| ~ 1 g, gyro ~ 0.
import time, board
i2c = board.i2c()
print("I2C scan:", [hex(a) for a in i2c.scan()], "(esperado 0x6b)")
imu = board.imu(i2c)
for _ in range(20):
    ax, ay, az, gx, gy, gz = imu.read_all()
    print("acc %.2f %.2f %.2f | gyro %.1f %.1f %.1f" % (ax, ay, az, gx, gy, gz))
    time.sleep_ms(250)
