# IMU QMI8658: inclina/agita la placa. En reposo: |a| ~ 1 g (o 9.8 m/s2 segun driver), gyro ~ 0.
import time, board
imu = board.imu()
print("data_ready:", imu.data_ready)
for _ in range(20):
    ax, ay, az, gx, gy, gz = imu.read_all()
    print("acc %.2f %.2f %.2f | gyro %.1f %.1f %.1f" % (ax, ay, az, gx, gy, gz))
    time.sleep_ms(250)
