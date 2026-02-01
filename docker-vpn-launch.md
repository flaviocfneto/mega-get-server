# Running mega-get-server behind Gluetun VPN

To send all MEGA traffic through the VPN, run mega-get-server using the VPN container’s network.

## 1. Expose port 8080 on the VPN container

In your Gluetun compose file, add `8080:8080` to the `protonvpn` service `ports` so the host can reach the app:

```yaml
    ports:
      - 49893:49893
      - 8080:8080   # add this for mega-get-server
```

Recreate the VPN container:

```bash
docker compose up -d protonvpn
```

## 2. Run mega-get-server on the VPN network

Start mega-get-server attached to the running `protonvpn` container (no `--publish`; it uses protonvpn’s network and the port you exposed above):

```bash
docker run \
  --detach \
  --restart unless-stopped \
  --name mega-get-server \
  --network container:protonvpn \
  --volume /path/to/downloads:/data/ \
  gm0n3y2503/mega-get-server:latest
```

Replace **/path/to/downloads** with your host path for MEGA downloads. Then open `http://YOUR_HOST_OR_IP:8080/` (use the hostname or IP of the machine running the container). No EXTERNAL_HOST or EXTERNAL_PORT is needed; the UI is served from the same origin.

---

## Optional: run both from the same compose

You can define mega-get-server in the same compose and bind it to the VPN service:

```yaml
version: '3.8'

services:
  protonvpn:
    image: docker.io/qmcgaw/gluetun:latest
    container_name: protonvpn
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - VPN_SERVICE_PROVIDER=protonvpn
      - VPN_TYPE=openvpn
      - OPENVPN_USER=XXX
      - OPENVPN_PASSWORD=XXX
      - VPN_PORT_FORWARDING=on
      - SERVER_COUNTRIES=Switzerland,Denmark
      - PORT_FORWARD_ONLY=on
      - VPN_PORT_FORWARDING_UP_COMMAND=/bin/sh -c '/usr/bin/wget -O- --retry-connrefused --post-data "json={\"listen_port\":{{PORTS}}}" http://127.0.0.1:49893/api/v2/app/setPreferences 2>&1'
    volumes:
      - /home/flav/DOCKER/appdata/qbittorrent-vpn/vpn:/gluetun
    ports:
      - 49893:49893
      - 8080:8080
    restart: unless-stopped

  mega-get-server:
    image: gm0n3y2503/mega-get-server:latest
    network_mode: "service:protonvpn"
    volumes:
      - /path/to/downloads:/data/
    restart: unless-stopped
    depends_on:
      - protonvpn
```

Replace `/path/to/downloads` with your host path. Start with:

```bash
docker compose up -d
```

---

## Example: same stack as qBittorrent (port 8383, /media/misatosStash)

Add **mega-get-server** to your existing Gluetun + qBittorrent compose like this.

**1. In `protonvpn`, add the mega-get port** (host 8383 → container 8080):

```yaml
  protonvpn:
    # ... rest unchanged ...
    ports:
      - 49893:49893
      - 8383:8080   # mega-get-server (same pattern as qbittorrent using 49893)
```

**2. Add the `mega-get-server` service** (same style as qbittorrent):

```yaml
  mega-get-server:
    image: gm0n3y2503/mega-get-server:latest
    container_name: mega-get-server
    depends_on:
      - protonvpn
    volumes:
      - /media/misatosStash:/data/
    network_mode: "service:protonvpn"
    restart: unless-stopped
```

Then:

```bash
docker compose up -d
```

- **URL:** `http://localhost:8383/` (or `http://YOUR_HOST_IP:8383` from another machine)
- **Downloads:** `/media/misatosStash`
- No EXTERNAL_HOST or EXTERNAL_PORT is needed; the Flet UI is served from the same origin.

Open the UI from any machine at http://HOST_IP:8383; no EXTERNAL_HOST/EXTERNAL_PORT needed.
