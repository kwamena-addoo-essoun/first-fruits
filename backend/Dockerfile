FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy the pre-built React bundle.
# main.py resolves: Path(__file__).parent.parent / "frontend" / "build"
# With WORKDIR=/app, that resolves to /frontend/build inside the container.
COPY frontend/build/ /frontend/build/

EXPOSE 8002

ENTRYPOINT ["sh", "entrypoint.sh"]
