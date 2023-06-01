FROM python:3.7.16

RUN mkdir -p /LogReader/

COPY requirements.txt /LogReader/requirements.txt
RUN pip install -r /LogReader/requirements.txt

COPY LogReader /LogReader/LogReader
COPY testLogReader /LogReader/testLogReader
COPY ui /LogReader/ui
COPY api.md /LogReader/api.md

WORKDIR /LogReader

CMD [ "python", "-m", "LogReader.app" ]
