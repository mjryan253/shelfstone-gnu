# 1. Start from a base image that already has Python 3.9 installed.
FROM python:3.9-slim

# 2. Set environment variables to prevent interactive prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# 3. Install Calibre and its system dependencies.
# Update package manager, install tools needed by the Calibre installer (wget, xz-utils),
# and other common utilities.
# Then, download and run the official Calibre installer script.
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    libstdc++6 \
    libglib2.0-0 \
    libउंट-2.0-0 \
    libgl1-mesa-glx \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    # Add any other specific dependencies Calibre might need on a slim image
 && wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 4. Set up the application directory inside the container.
WORKDIR /app

# 5. Copy the requirements file and install Python packages.
# This is done before copying all source code to leverage Docker layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the project's source code into the container.
# This assumes your application structure within calibre_api/ is like:
# calibre_api/
#   app/
#     main.py
#     crud.py
#     models.py
#   requirements.txt
#   Dockerfile
# The COPY . . in the original main.dockerfile was relative to the repo root.
# Here, the build context will be calibre_api/, so COPY . . is appropriate.
COPY . .

# 7. Expose the port the app runs on.
# Based on calibre_api/app/main.py comments, it runs on 6336.
EXPOSE 6336

# 8. Define the command to run when the container starts.
# The FastAPI app object is 'app' in 'app.main'.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6336"]
