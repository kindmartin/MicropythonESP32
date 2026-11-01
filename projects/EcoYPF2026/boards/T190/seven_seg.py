# seven_seg.py
# Renderizador de texto para las fuentes font_to_py (fonts/seven_segment_*)
# sobre nuestro driver drivers/tft170.TFT170 (API blit() con framebuf.FrameBuffer,
# distinta de la blit_buffer() de st7789py.py que usa font_demo.py).

import framebuf


def char_width(font, ch):
    _, _, w = font.get_ch(ch)
    return w


def text_width(font, text):
    """Ancho total en px de un string con esta fuente."""
    total = 0
    for ch in text:
        total += char_width(font, ch)
    return total


def _render_char(font, ch, fg, bg):
    """Construye un framebuf.FrameBuffer RGB565 para un caracter."""
    data, h, w = font.get_ch(ch)
    bpr = (w - 1) // 8 + 1
    fh, fl = fg >> 8, fg & 0xFF
    bh, bl = bg >> 8, bg & 0xFF
    buf = bytearray(w * h * 2)
    for row in range(h):
        row_off = row * bpr
        for col in range(w):
            byte = data[row_off + col // 8]
            bit = (byte >> (7 - (col % 8))) & 1
            i = (row * w + col) * 2
            if bit:
                buf[i], buf[i + 1] = fh, fl
            else:
                buf[i], buf[i + 1] = bh, bl
    fbuf = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
    return fbuf, w, h


def draw_text(tft, font, text, x, y, fg, bg=0x0000):
    """Dibuja 'text' con 'font' en (x,y) sobre tft (drivers.tft170.TFT170).
    Devuelve la coordenada x final (util para encadenar texto)."""
    cx = x
    for ch in text:
        fbuf, w, h = _render_char(font, ch, fg, bg)
        tft.blit(fbuf, cx, y)
        cx += w
    return cx


def draw_text_centered(tft, font, text, y, fg, bg=0x0000, width=None):
    """Centra 'text' horizontalmente en el ancho dado (por defecto tft.width)."""
    width = width if width is not None else tft.width
    tw = text_width(font, text)
    x = max(0, (width - tw) // 2)
    return draw_text(tft, font, text, x, y, fg, bg)
