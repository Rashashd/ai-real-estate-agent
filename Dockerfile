FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY schemas.py .
COPY prompts.py .
COPY llm_client.py .
COPY model/ ./model/
# pass GROQ_API_KEY at runtime via --env-file .env

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]