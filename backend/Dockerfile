# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies for Chrome + unzip + Selenium
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip \
    libglib2.0-0 libnss3 libgconf-2-4 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libasound2 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libxss1 \
    libappindicator3-1 xdg-utils \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install Google Chrome stable
RUN apt-get update && \
    apt-get install -y \
    wget \
    gnupg \
    curl \
    fonts-liberation \
    libgbm1 \
    libvulkan1 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libnspr4 \
    libnss3 \
    lsb-release \
    xdg-utils \
    && \
    wget -q -O chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./chrome.deb && \
    rm chrome.deb

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Copy local ChromeDriver to a known location
RUN chmod +x crawler/chromedriver-linux64/chromedriver && \
    cp crawler/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver

# Create a non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser && \
    chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose Django port
EXPOSE 8000

# Run server (note: worker sẽ override bằng CMD riêng nếu cần)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
