FROM python:3.9-slim-buster

ADD . /root

WORKDIR /root

RUN python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple
RUN pip install jinja2 flask pymupdf -i https://mirrors.aliyun.com/pypi/simple

EXPOSE 5000

CMD ["python","app.py"]