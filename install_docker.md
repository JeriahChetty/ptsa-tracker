# Docker Installation Instructions

1. Download Docker Desktop for Windows from [Docker's official website](https://www.docker.com/products/docker-desktop)
2. Run the installer and follow the prompts
3. Ensure WSL 2 is enabled if prompted
4. Restart your computer after installation
5. Start Docker Desktop from the Start menu
6. Wait for Docker to completely start
7. Open PowerShell and run your command again:

```
docker compose up -d --build
```

Note: The newer Docker CLI uses `docker compose` (with a space) instead of `docker-compose`.
