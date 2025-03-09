# Use official Python image
FROM python:3.10

# Create a non-root user and group
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Change ownership of app directory
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose Django port
EXPOSE 8000

# Run server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
