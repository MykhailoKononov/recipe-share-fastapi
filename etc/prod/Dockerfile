FROM python:3.12-slim AS builder

# system update & package install
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ../../ .
WORKDIR .

RUN python3 -m pip install --user --upgrade pip && \
    python3 -m pip install -r requirements.txt

CMD ["python", "main.py"]