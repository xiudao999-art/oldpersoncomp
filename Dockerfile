FROM python:3.10

WORKDIR /app

# Copy all files to the container
COPY . .

# Install dependencies
# Since we copied everything, the local path ./libs/... in requirements.txt will resolve correctly
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7860 (Hugging Face Spaces default for Docker)
EXPOSE 7860

# Run Streamlit
CMD ["streamlit", "run", "web_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
