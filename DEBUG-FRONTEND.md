# Debugging the mega-get-server frontend

Use these steps to find why the web UI doesn’t work while `mega-get` works in the container.

**Stack:** The frontend is a Flet (Python) web app served on port 8080. No EXTERNAL_HOST or EXTERNAL_PORT is needed; the UI is served from the same origin.

---

## 1. Check that the processes are running

```bash
docker exec mega-get-server ps aux
```

You should see:

- `mega-cmd-server`
- `python` (or `python3`) running `/app/main.py` (Flet app)

If the **Python/Flet** process is missing, it may have crashed. Check logs (step 2).

---

## 2. Check container logs

```bash
docker logs mega-get-server 2>&1
```

Look for:

- Errors from the Flet app (e.g. “address already in use”, permission errors).
- Any line that might show why the entrypoint or websocketd failed.

If you run with `--network container:protonvpn`, the VPN container owns port 8080 in the shared network. Only one service can listen on 8080; if something else in that stack uses 8080, the Flet app will fail to bind.

---

## 3. Check that port 8080 is listening

```bash
docker exec mega-get-server ss -tlnp
```

(or `netstat -tlnp` if `ss` isn’t available)

You should see something like:

```text
LISTEN  0  128  *:8080  *:*  users:(("python",...))
```

If 8080 is not listed, the Flet app didn’t bind (crashed or wrong port).

---

## 4. Test HTTP from inside the container

```bash
docker exec mega-get-server curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/
```

- **200** – HTTP and Flet UI work inside the container.
- **000** or connection error – nothing is listening on 8080, or curl isn’t in the image (then try from the host, step 5).

---

## 5. Test from the host

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8383/
```

(Use the host/port you actually use: e.g. `http://192.168.1.x:8383` if you’re on another machine.)

- **200** – The frontend is reachable; problem is likely WebSocket or browser (steps 7–8).
- **000** / connection refused – Port not published or wrong host/port:
  - Standalone: container must be run with `-p 8383:8080`.
  - Behind Gluetun: `protonvpn` must have `8383:8080` in `ports`, and mega-get-server must use `network_mode: "service:protonvpn"` (or `--network container:protonvpn`).

---

## 6. WebSocket URL (Flet)

The Flet app serves UI and WebSocket from the same origin. No EXTERNAL_HOST or EXTERNAL_PORT is needed. If the page loads but the UI does not update, check the browser console (step 8) for WebSocket errors.

---

## 7. Browser: Network tab

1. Open the UI (e.g. `http://localhost:8383/`).
2. Open DevTools (F12) → **Network**.
3. Reload.

Check:

- The main page – status 200. If 404 or failed, the Flet app or port is wrong (recheck steps 3–5).
- A request with type **websocket** (or “WS”) – status **101 Switching Protocols**. If it’s red/failed: mixed content, or proxy/firewall blocking WebSockets.

---

## 8. Browser: Console

In DevTools → **Console**, look for:

- `WebSocket connection to 'ws://...' failed` – network or port issue (steps 5–6).
- Other JavaScript errors – can point to a broken page or script.

---

## 9. Typical fixes

| Symptom | What to try |
|--------|--------------|
| Page never loads (connection refused) | Correct `-p 8383:8080` or Gluetun `8383:8080`; mega-get-server on same network as protonvpn. |
| Page loads, WebSocket fails | Check network/firewall; Flet serves same origin so no EXTERNAL_HOST/EXTERNAL_PORT. |
| “Address already in use” in logs | Only one process can use 8080 in the shared network; stop anything else using 8080 in that stack. |
| Python/Flet not in `ps` | Check full `docker logs`; ensure no env/volume issue preventing startup. |

---

## 10. Quick “from scratch” test (standalone)

To rule out Gluetun/network mode, run the app standalone and open the UI:

```bash
docker run -d --name mega-get-test \
  -p 8383:8080 \
  -v /media/misatosStash:/data/ \
  gm0n3y2503/mega-get-server:latest
```

Then:

```bash
docker exec mega-get-test ps aux
docker exec mega-get-test ss -tlnp
curl -s -o /dev/null -w "%{http_code}" http://localhost:8383/
```

If this works but the Gluetun setup doesn’t, the issue is port publishing (8383:8080 on protonvpn) when using `network_mode: service:protonvpn`.
