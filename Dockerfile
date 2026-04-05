FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Step 1 — Install numpy first (must be 1.x)
RUN pip install --no-cache-dir "numpy==1.26.4"

# Step 2 — Install PyTorch CPU (separate index)
RUN pip install --no-cache-dir "torch==2.1.0" \
    --index-url https://download.pytorch.org/whl/cpu

# Step 3 — Install transformers + sentence-transformers (PyPI)
RUN pip install --no-cache-dir \
    "transformers==4.40.2" \
    "sentence-transformers==2.7.0"

# Step 4 — Rest of dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5 — Pre-download NLP model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy app
COPY --chown=user *.py ./

ENV PORT=7860
ENV ENV=production

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]