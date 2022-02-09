FROM python:3.7.6

RUN mkdir -p /static_time_series_resource
RUN mkdir -p /init
RUN mkdir -p /logs
RUN mkdir -p /domain-messages
RUN mkdir -p /domain-tools

# install the python libraries
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

COPY static_time_series_resource/ /static_time_series_resource/
COPY init/ /init/
COPY domain-messages/ /domain-messages/
COPY domain-tools/ /domain-tools/

WORKDIR /

CMD [ "python3", "-u", "-m", "static_time_series_resource.component" ]
