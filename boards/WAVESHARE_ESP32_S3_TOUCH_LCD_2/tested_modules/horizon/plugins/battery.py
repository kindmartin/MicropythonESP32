# Bateria cada 2 s -> app.state["bat_pct"], ["bat_present"].
import uasyncio as asyncio
import board


def setup(app):
    app.state.update(bat_pct=0, bat_present=True)

    async def task(app):
        while True:
            v = board.vbat()
            app.state["bat_present"] = v > 2.8
            app.state["bat_pct"] = max(0, min(100, int((v - 3.3) / (4.2 - 3.3) * 100)))
            await asyncio.sleep(2)

    app.add_task("battery", task)
