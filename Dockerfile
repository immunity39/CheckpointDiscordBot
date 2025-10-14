FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
COPY app/bot.py ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

CMD ["python", "bot.py"]
