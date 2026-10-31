FROM python:3.12-slim
WORKDIR /app
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ ./
COPY samples/ /samples/
CMD ["python", "app.py"]
