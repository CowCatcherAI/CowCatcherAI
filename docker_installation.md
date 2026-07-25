
## 🐳 Docker (Advanced — older GPUs or Linux/NAS)

Use Docker if you have no GPU, or want to run this on a server or NAS.

**Requirements:** Docker Compose + NVIDIA Container Toolkit (for GPU support)

1. Create a `compose.yml` file:

```yaml
services:
  aidetector:
    image: "ghcr.io/eschouten/ai-detector:latest"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./detections:/app/detections
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
```

2. Place your [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0) in the same folder
3. Run:

```bash
docker compose up -d
docker compose logs -f aidetector
```
