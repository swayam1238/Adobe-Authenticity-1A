# Specify the platform to ensure compatibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script and other necessary files into the container
COPY main.py .

# Define the command to run when the container starts
# This will execute the main.py script to process the PDFs
CMD ["python", "main.py"]
