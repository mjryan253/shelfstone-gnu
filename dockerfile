# 1. Start from a base image that already has Python 3.9 installed.
# Using a "slim" version keeps the image size smaller.
FROM python:3.9-slim

# 2. Install Calibre and its system dependencies.
# This command first updates the package manager, then installs tools
# needed by the Calibre installer (like wget and xz-utils).
# Finally, it downloads and runs the official Calibre installer script.
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
 && wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# 3. Set up the application directory inside the container.
WORKDIR /app

# 4. Copy the project's source code into the container.
# This includes Jules's Python files and your requirements.txt.
COPY . .

# 5. Install the required Python packages for your project.
RUN pip install --no-cache-dir -r requirements.txt

# 6. Define the command to run when the container starts.
# This example assumes your main file is "main.py" and the FastAPI app is named "app".
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]