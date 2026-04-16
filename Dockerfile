FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY schemas.py .
COPY prompts.py .
COPY llm_client.py .
COPY prompt_eval.py .
COPY ui.py .
COPY model/ ./model/
# note: pass GROQ_API_KEY at runtime via: docker run -e GROQ_API_KEY=... or --env-file .env

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]