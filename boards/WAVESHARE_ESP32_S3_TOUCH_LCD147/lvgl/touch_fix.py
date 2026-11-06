# Orientacion del touch AXS5106L para el firmware LVGL (usa el mecanismo touch_cal de pointer_framework; no escribe en NVS).
# El demo de Waveshare invierte x en vertical (x = 171 - xraw); el driver de lvgl_micropython no: sin esto el touch sale espejado en x.
# Si tras probar sigue mal, cambia las banderas: MIRROR_X / MIRROR_Y / SWAP_XY (SWAP_XY intercambia ejes antes de espejar).
MIRROR_X = True
MIRROR_Y = False
SWAP_XY = False


class _Cal:
    def __init__(self, mirror_x, mirror_y, swap):
        self.alphaX = 0.0 if swap else 1.0
        self.betaX = 1.0 if swap else 0.0
        self.deltaX = 0.0
        self.alphaY = 1.0 if swap else 0.0
        self.betaY = 0.0 if swap else 1.0
        self.deltaY = 0.0
        self.mirrorX = mirror_x
        self.mirrorY = mirror_y

    def save(self):
        pass


def make(mirror_x=MIRROR_X, mirror_y=MIRROR_Y, swap=SWAP_XY):
    return _Cal(mirror_x, mirror_y, swap)


CAL = make()
