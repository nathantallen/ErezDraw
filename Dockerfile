FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libxrender1 libxext6 libsm6 libexpat1 && rm -rf /var/lib/apt/lists/*
COPY web/requirements.txt /app/web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt
COPY chemistry.py structure_ops.py ligands.py glassware.py template_catalog.py mass_spec.py nmr_models.py nmr_spectrum.py chemdraw_io.py /app/
COPY assets /app/assets
COPY web /app/web
COPY COPYING THIRD-PARTY-NOTICES.md /app/
RUN chmod -R a+rX /app && useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "web.server:app"]
