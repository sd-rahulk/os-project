param([string]$Host = "127.0.0.1", [int]$Port = 8765)
python -m uvicorn apps.server.app.main:app --host $Host --port $Port

