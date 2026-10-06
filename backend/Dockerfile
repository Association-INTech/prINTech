FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Variable d'environnement pour accélérer uv dans Docker
ENV UV_COMPILE_BYTECODE=1

# Copie des fichiers de configuration de dépendances
COPY pyproject.toml uv.lock* ./

# Installation des dépendances du projet
RUN uv sync --no-install-project

# Copie du reste du code backend
COPY . .

# Installation du projet lui-même
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "./manage.py", "runserver", "0.0.0.0:8000"]