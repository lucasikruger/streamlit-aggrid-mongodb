FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .

RUN pip3 install -r requirements.txt

# Set umask
RUN echo "umask 002" >> /etc/profile

# Changing permissions of existing files
RUN chmod -R 777 /app
EXPOSE 8501
