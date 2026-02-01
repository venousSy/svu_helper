FROM node:18-alpine

WORKDIR /app

COPY web/package.json web/package-lock.json* ./
RUN npm install

COPY web/ .

EXPOSE 3000
# Start Vite on the assigned PORT (Railway requirement)
CMD sh -c "npm run dev -- --host --port ${PORT:-3000}"
