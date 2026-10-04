FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

# Need to run it on 8002 or whatever is appropriate. 
# Looking at main.py, it's just FastAPI. Using uvicorn on port 8002.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
