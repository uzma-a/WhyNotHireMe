FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Pin exact compatible versions — tested combination
RUN pip install --no-cache-dir \
    "numpy==1.26.4" \
    "torch==2.1.0" --index-url https://download.pytorch.org/whl/cpu \
    "transformers==4.40.0" \
    "sentence-transformers==2.7.0"

# Install rest of dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLP model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy app code
COPY --chown=user *.py ./

ENV PORT=7860
ENV ENV=production

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]