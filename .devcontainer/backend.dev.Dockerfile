FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN apk update && \
    apk add --no-cache --upgrade bash && \
    apk add --no-cache postgresql-client ffmpeg && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \ 
    apk add --no-cache git

COPY .devcontainer/backend.entrypoint.dev.sh /usr/local/bin/entrypoint.sh
RUN chmod a+x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]