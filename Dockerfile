FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python scripts/build_replay_dataset.py && python -m src.ingestion.run --mode replay --speed instant && python -m src.engine.run && python -m src.modules.rebalancer.run && python -m src.modules.stress.run && python -m src.evaluation.run

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "src/dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
