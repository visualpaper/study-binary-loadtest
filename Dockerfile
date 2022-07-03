FROM python:3.8-alpine

RUN    pip install -U setuptools \
    && pip install locust==2.10.1  \
    && mkdir /locust

ADD ./locust.py /locust/locust.py
ADD ./apis /locust/apis
ADD ./actions /locust/actions
ADD ./datas /locust/datas

EXPOSE 8089 5557 5558
ENTRYPOINT ["/usr/local/bin/locust", "-f", "/locust/locust.py"]
