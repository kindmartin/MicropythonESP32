"""Minimal HTTP dashboard served by the paddock access point."""

import ujson
import network
import uasyncio as asyncio

import HW


_PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Telemetría EcoYPF</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101820;color:#f4f7fa;
font:16px system-ui,sans-serif}main{max-width:760px;margin:auto;padding:20px}
h1{font-size:1.5rem;margin:0 0 6px}.sub{color:#aab8c4;margin:0 0 20px}
#status{padding:10px 12px;border-radius:8px;background:#263541;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}
.card{background:#1d2a34;border:1px solid #344550;border-radius:10px;padding:13px}
.label{display:block;color:#aab8c4;font-size:.85rem}.value{font-size:1.45rem;
font-weight:650;margin-top:5px}.unit{font-size:.85rem;color:#aab8c4}
footer{color:#91a0ab;font-size:.8rem;margin-top:18px}
</style></head><body><main>
<h1>Telemetría EcoYPF</h1><p class="sub">Receptor LoRa · XIAO ESP32-S3</p>
<div id="status">Conectando…</div><section id="cards" class="grid"></section>
<footer id="meta"></footer></main>
<script>
const cards=[
 ['speed_kmh','Velocidad','km/h'],['whkm_avg','Consumo medio','Wh/km'],
 ['current_a','Corriente','A'],['battery_pack_v','VBATS total','V'],
 ['battery_1_v','Batería 1','V'],
 ['battery_2_v','Batería 2','V'],['battery_3_v','Batería 3','V'],
 ['battery_4_v','Batería 4','V'],['power_w','Potencia','W'],
 ['power_avg_w','Potencia media','W'],['distance_m','Distancia','m'],
 ['whkm_inst','Consumo instantáneo','Wh/km'],['wh_total','Energía','Wh']];
const fmt=(n)=>Number(n).toLocaleString('es-AR',{maximumFractionDigits:2});
async function refresh(){
 try{
  const r=await fetch('/api',{cache:'no-store'});const d=await r.json();
  document.getElementById('cards').innerHTML=cards.map(([k,l,u])=>
   '<article class="card"><span class="label">'+l+'</span><div class="value">'+
   (d.values[k]===undefined?'—':fmt(d.values[k]))+
   ' <span class="unit">'+u+'</span></div></article>').join('');
  let packetAge=d.packet_age_ms===null?null:Math.floor(d.packet_age_ms/1000);
  let sourceAge=d.source_age_ms===null?null:Math.floor(d.source_age_ms/1000);
  let text=d.rx_count?'LoRa: '+(packetAge<8?'recibiendo':'sin paquetes recientes')+
   ' · paquete hace '+packetAge+' s':'Esperando el primer paquete LoRa…';
  if(d.rx_count && sourceAge!==null){
   text+=' · origen '+(d.source_fresh?'actualizado':'vencido')+' hace '+sourceAge+' s';
  }
  if(d.rx_count && (!d.adc_valid || !d.current_valid)){
   text+=' · sensores: '+(!d.adc_valid?'tensión inválida ':'')+
    (!d.current_valid?'corriente inválida':'');
  }
  if(!d.radio_ok)text='Radio LoRa no disponible'+(d.radio_error?': '+d.radio_error:'');
  document.getElementById('status').textContent=text;
  document.getElementById('meta').textContent='Paquetes recibidos: '+d.rx_count+
   (d.last_error?' · Último paquete inválido: '+d.last_error:'');
 }catch(e){document.getElementById('status').textContent='Error consultando telemetría';}
}
refresh();setInterval(refresh,1000);
</script></body></html>"""


class DashboardServer:
    def __init__(self, state):
        self._state = state
        self._ap = network.WLAN(network.AP_IF)
        self._server = None

    async def start(self):
        self._ap.active(True)
        self._ap.config(essid=HW.AP_SSID, password=HW.AP_PASSWORD, authmode=3)
        self._ap.ifconfig((
            HW.AP_IP, HW.AP_NETMASK, HW.AP_IP, HW.AP_IP,
        ))
        self._server = await asyncio.start_server(
            self._handle_client, "0.0.0.0", 80)
        print("[wifi] AP protegido {} listo en http://{}/".format(
            HW.AP_SSID, HW.AP_IP))

    async def stop(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._ap.active(False)
        print("[wifi] AP detenido")

    async def _handle_client(self, reader, writer):
        try:
            request = await reader.readline()
            while True:
                header = await reader.readline()
                if header in (b"", b"\r\n", b"\n"):
                    break
            parts = request.decode("ascii").strip().split()
            path = parts[1] if len(parts) > 1 else "/"
            if path == "/api":
                body = ujson.dumps(self._state.as_dict()).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif path == "/" or path == "/index.html":
                body = _PAGE.encode("utf-8")
                content_type = "text/html; charset=utf-8"
            else:
                body = b"Not found"
                content_type = "text/plain; charset=utf-8"
            status = "200 OK" if path in ("/", "/index.html", "/api") else "404 Not Found"
            response = (
                "HTTP/1.1 {}\r\n"
                "Content-Type: {}\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n"
                "Cache-Control: no-store\r\n\r\n"
            ).format(status, content_type, len(body))
            writer.write(response.encode("ascii"))
            writer.write(body)
            await writer.drain()
        except (OSError, UnicodeError) as exc:
            print("[http] cliente desconectado:", exc)
        finally:
            writer.close()
