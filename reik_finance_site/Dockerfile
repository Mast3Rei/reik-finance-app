FROM python:3.10-alpine
ENV PYTHONUNBUFFERED 1

WORKDIR /reik_finance_docker
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python manage.py runserver 0.0.0.0:80