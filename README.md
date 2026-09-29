# ERP VIBE CODING

This repository contains a lightweight ERP prototype with FastAPI backend, MySQL persistence, and Docker Compose support.

## Start the system

Use Docker Compose from the project root:

```powershell
docker-compose up --build -d
.\scripts\ci_healthcheck.ps1 -wait 60
```

or on Linux/macOS:

```bash
docker-compose up --build -d
./scripts/ci_healthcheck.sh --wait 60
```

After startup, open `http://127.0.0.1:8000/docs`.

## Stop the system

```powershell
docker-compose down --volumes --remove-orphans
```

## Notes

The backend uses `backend/Dockerfile` and `docker-compose.yml` to run MySQL and the FastAPI service.
