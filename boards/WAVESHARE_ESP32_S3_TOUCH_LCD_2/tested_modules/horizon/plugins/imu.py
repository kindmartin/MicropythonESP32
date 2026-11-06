# Lee el IMU (QMI8658) y alimenta el filtro del overlay.
import uasyncio as asyncio
import board


def setup(app):
    import qmi8658
    app.state["acc"] = (0.0, 0.0, 1.0)
    imu = qmi8658.QMI8658(app.hw("i2c", board.i2c))

    async def task(app):
        while True:
            try:
                d = imu.read_all()          # ax ay az gx gy gz
                app.state["acc"] = d[:3]
                app.ov.update_imu(d[:3], d[3:])
            except OSError:
                pass
            await asyncio.sleep_ms(10)

    app.add_task("imu", task)
