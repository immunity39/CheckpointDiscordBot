FROM python:3.12-slim

COPY requirements.txt /usr/src/app/
COPY app/bot.py /usr/src/app/

RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

EXPOSE 3000

CMD ["python", "/usr/src/app/bot.py", "-m", "http.server", "3000"]
