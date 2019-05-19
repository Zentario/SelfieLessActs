FROM alpine:3.7

RUN apk add --no-cache python3

RUN pip3 install --upgrade pip

RUN apk add build-base

WORKDIR /act_management

COPY . /act_management

RUN pip3 install Flask

RUN pip3 install Flask-Cors

RUN pip3 install requests

ENV TEAM_ID=CC_085_102_117_119

EXPOSE 80

CMD python3 acts.py

# ENTRYPOINT ["python3"]

# CMD ["acts.py"]