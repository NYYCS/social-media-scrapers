FROM python:3

WORKDIR /usr/src/app

COPY dianping-requirements.txt ./
RUN pip3 install --no-cache-dir -r dianping-requirements.txt

COPY . .

CMD [ "scrapy", "runspider", "dianping.py", "-o", "dianping.csv"]