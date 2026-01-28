FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CORS_ALLOWED_ORIGINS="http://localhost:4200"
ENV CSRF_TRUSTED_ORIGINS="http://localhost:4200"
ENV DEBUG=False

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Copy project
COPY . /app/

# Make start script executable
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Entrypoint
CMD ["/app/start.sh"]
