# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Separate build stage keeps the final image lean.
# Build tools (gcc, pip cache) stay in this stage — not in production image.
FROM python:3.14-slim AS builder

WORKDIR /app

# Install build dependencies
# These are needed to compile psycopg2, Pillow etc.
# Only in builder stage — not copied to final image
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
# ── Why copy requirements first? ─────────────────────────────────────────────
# Docker caches each layer. If requirements.txt hasn't changed,
# this layer is reused — pip install doesn't re-run on every build.
# Saves 2-3 minutes per deploy.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt


# ── Stage 2: Production ───────────────────────────────────────────────────────
FROM python:3.14-slim

WORKDIR /app

# Runtime dependencies only — no build tools
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Copy entrypoint script and make executable
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Why create a non-root user? ───────────────────────────────────────────────
# Running as root inside containers is a security risk.
# If the container is compromised, attacker gets root on the host.
# Industry standard: always run apps as non-root user.
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# ↑ PYTHONUNBUFFERED — logs appear immediately, not buffered
# ↑ PYTHONDONTWRITEBYTECODE — no .pyc files, cleaner image

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]