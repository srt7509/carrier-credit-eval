FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

EXPOSE 5001

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
