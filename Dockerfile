FROM python:3.12-slim
WORKDIR /workspace
COPY pyproject.toml ./
COPY rag_workbench ./rag_workbench
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "rag_workbench.api:app", "--host", "0.0.0.0", "--port", "8000"]
