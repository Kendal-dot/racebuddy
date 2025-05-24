FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Kopiera requirements från backend root
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera app-koden
COPY . /app/

# Kör bara API:t för nu (skippa RAG ingestion tills vi har data)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]