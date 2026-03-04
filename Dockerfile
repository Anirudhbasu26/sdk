FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY examples/fullstack/ examples/fullstack/

EXPOSE 7860

CMD ["uvicorn", "examples.fullstack.server:app", "--host", "0.0.0.0", "--port", "7860"]
