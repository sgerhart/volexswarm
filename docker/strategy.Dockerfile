FROM python:3.11-slim
WORKDIR /app
COPY ./agents/strategy /app
COPY ./common /app/common
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
