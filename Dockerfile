FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
COPY app/bot.py /usr/src/app/
COPY health_check.py /usr/src/app/
COPY run_all.sh /usr/src/app/

RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
RUN chmod +x /usr/src/app/run_all.sh

EXPOSE 3000

CMD ["python", "/usr/src/app/bot.py", "--host", "0.0.0.0", "--port", "3000"]
