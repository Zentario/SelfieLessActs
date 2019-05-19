FROM alpine:3.7

RUN apk add --no-cache python3

RUN pip3 install --upgrade pip

RUN apk add build-base

WORKDIR /user_management

COPY . /user_management

RUN pip3 install Flask

RUN pip3 install Flask-Cors

RUN pip3 install requests

ENV TEAM_ID=CC_085_102_117_119

EXPOSE 80

ENTRYPOINT ["python3"]

CMD ["users.py"]