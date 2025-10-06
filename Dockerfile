FROM node:20-slim

WORKDIR /app

COPY app/ .

RUN npm install

EXPOSE 3000

CMD ["node", "main.mjs"]
