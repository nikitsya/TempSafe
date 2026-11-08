FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend/ backend/
RUN python -m pip install --no-cache-dir .
COPY frontend/ frontend/
CMD ["python", "-m", "uvicorn", "tempsafe.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
