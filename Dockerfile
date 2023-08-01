FROM python:3.9-slim

RUN mkdir /app
WORKDIR /app

# Install pip and poetry
RUN pip install --no-cache --upgrade pip
RUN pip install --no-cache "poetry>=1.2.2,<1.3.0"

# Create layer for dependencies
COPY poetry.lock pyproject.toml ./

# Install python dependencies
RUN poetry export --with dev > requirements.txt
RUN pip install --no-cache -r requirements.txt

# Copy files to image
COPY data ./data
COPY src ./src

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]