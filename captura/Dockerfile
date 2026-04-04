FROM python:3.11

WORKDIR /app

COPY requirements.txt .
COPY .env .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "python app/crearDB.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
