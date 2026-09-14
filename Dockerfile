FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
WORKDIR /app/backend
ENV TELEMETRY_MODE=simulation
ENV FRONTEND_ORIGIN=https://kvigneshsivan-bot.github.io
EXPOSE 7860
CMD uvicorn app.main:app --host 0.0.0.0 --port 7860
