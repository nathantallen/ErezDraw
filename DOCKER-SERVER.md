# ErezDraw Docker server package

Linux amd64 image. Requires Docker Engine and Compose v2.

Download ErezDraw-Docker-linux-amd64.tar.gz and compose.yaml into a new directory on your server, such as /opt/erezdraw.

```bash
docker load -i ErezDraw-Docker-linux-amd64.tar.gz
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8088/health
```

Open http://SERVER-IP:8088. The default port avoids ErezOps on 8080 and Seer on 5055. To change it, set EREZDRAW_PORT before running Compose.

The container runs as a non-root user with a read-only filesystem. Drawings are downloaded to the browser; the container has no persistent document volume. Keep the service on your trusted LAN or behind an authenticated reverse proxy; no login is built into this app. Do not expose the port publicly.

Desktop source: 1d19612e5a3c6a62e27a7861d0cea04864ebc763, plus Docker packaging fixes on the release branch. This package contains all 68 labware and 112 total template choices.
