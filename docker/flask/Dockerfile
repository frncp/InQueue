FROM python:3.8.5

ENV APP ../../app

RUN mkdir $APP
WORKDIR $APP

EXPOSE 80
EXPOSE 5000


COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "uwsgi", "--enable-threads", "--ini", "myproject.ini"]
