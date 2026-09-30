FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings_prod \
    PORT=7860

# Hugging Face runs containers as uid 1000
RUN useradd -m -u 1000 user
WORKDIR /app

# CPU-only PyTorch (~200 MB instead of ~2 GB), then the rest
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY . .
# start.sh must have Unix line endings (files edited on Windows may have CRLF)
RUN sed -i 's/\r$//' start.sh \
 && python manage.py collectstatic --noinput \
 && chown -R user:user /app

USER user
EXPOSE 7860
CMD ["sh", "start.sh"]
