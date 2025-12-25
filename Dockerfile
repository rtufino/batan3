FROM mcr.microsoft.com/devcontainers/python:3.12

# Instalar dependencias de sistema para PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/batan3

# Instalamos dependencias
COPY requirements.txt .
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Carpeta de historiocos de RooCode en VSCode (Eliminar en produccion)
RUN mkdir -p /home/vscode/.vscode-server/data/User/globalStorage && \
    chown -R vscode:vscode /home/vscode/.vscode-server
