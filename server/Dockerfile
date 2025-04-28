FROM python:3.13

WORKDIR /app
COPY server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ /app
CMD ["python", "app.py"]