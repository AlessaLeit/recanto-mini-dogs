FROM python:3.11-slim
WORKDIR /app

# Cria um usuário sem privilégios para rodar a aplicação
RUN useradd -m -r appuser

# Copia os requisitos e instala dependências do sistema e do Python em uma única camada
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y libpq-dev gcc curl -y && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Copia o código e define a propriedade para o usuário appuser
COPY --chown=appuser:appuser backend/ .

USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
