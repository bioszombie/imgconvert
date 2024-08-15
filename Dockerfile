FROM debian:bookworm-20240722-slim

# Metadata
LABEL org.opencontainers.image.title="Image to WebP Converter" \
      org.opencontainers.image.description="Converts images to WebP format with optimized size and quality for web usage." \
      org.opencontainers.image.authors="Bioszombie bioszombie@gmail.com" \
      org.opencontainers.image.source="https://github.com/bioszombie/imgconvert" \
      org.opencontainers.image.version="1.0" \
      org.opencontainers.image.licenses="MIT"

# Install ImageMagick, WebP, and inotify-tools
RUN apt-get update && \
    apt-get install -y imagemagick webp inotify-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a directory for your script and input/output folders
WORKDIR /app
COPY convert_to_webp.sh /app
RUN chmod +x convert_to_webp.sh

# Input, Output, Temporary, Error, and Log volume
VOLUME ["/app/input", "/app/output", "/app/tmp", "/app/error", "/app/log"]

# Set the script as the entrypoint
ENTRYPOINT ["./convert_to_webp.sh"]
