FROM python:3.11-slim

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /app

COPY . /app

CMD ["gunicorn", "-b 0.0.0.0:80", "app/app:server"]
