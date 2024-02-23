#!/bin/bash

# Ensure input, output, tmp, error, and log directories exist
mkdir -p /app/input /app/output /app/tmp /app/error /app/log

# Log files
ERROR_LOG="/app/log/errors.log"
SUCCESS_LOG="/app/log/success.log"

# Cleanup function
cleanup() {
    echo "Cleaning up /app/error and /app/log directories..."
    rm -rf /app/error/* /app/log/*
    echo "Cleanup done."
}

# Function to handle termination signal
handle_signal() {
    echo "Signal received, terminating..."
    cleanup
    exit 0
}

# Trap termination signals
trap 'handle_signal' SIGINT SIGTERM

# Function to convert a single image
convert_image() {
    local file="$1"
    echo "Starting processing of $file..."
    local filename=$(basename "$file")
    local output="/app/output/${filename%.*}.webp"
    local original_size=$(stat -c%s "$file")

    # Use ImageMagick to convert the image to WebP format with reduced size and quality
    if convert "$file" -resize 800x800 -quality 80 "$output" 2>>"$ERROR_LOG"; then
        local final_size=$(stat -c%s "$output")
        local reduction=$(awk "BEGIN {printf \"%.2f\", (($original_size - $final_size) / $original_size) * 100}")
        echo "$file ($original_size bytes) -> $output ($final_size bytes), Reduction: $reduction%" | tee -a "$SUCCESS_LOG"
        
        # Remove the original file after successful conversion
        rm "$file"
        echo "Successfully processed and removed $file"
    else
        echo "Error processing $file, moving to /app/error" | tee -a "$ERROR_LOG"
        mv "$file" "/app/error/$filename"
    fi
}

# Main loop
if ! command -v inotifywait &>/dev/null; then
    echo "inotifywait not found, falling back to polling mode."
    while true; do
        for file in /app/input/*; do
            if [ -f "$file" ]; then
                tmp_file="/app/tmp/$(basename "$file")"
                if ! mv "$file" "$tmp_file"; then
                    echo "Error moving $file to /app/tmp, moving to /app/error" | tee -a "$ERROR_LOG"
                    mv "$file" "/app/error/$(basename "$file")"
                    continue
                fi
                convert_image "$tmp_file" &
            fi
        done
        wait
        echo "Waiting for new files..."
        sleep 20
    done
else
    echo "Using inotifywait for file monitoring."
    inotifywait -m -e create -e moved_to --format '%w%f' /app/input | while read file; do
        if [ -f "$file" ]; then
            tmp_file="/app/tmp/$(basename "$file")"
            if ! mv "$file" "$tmp_file"; then
                echo "Error moving $file to /app/tmp, moving to /app/error" | tee -a "$ERROR_LOG"
                mv "$file" "/app/error/$(basename "$file")"
                continue
            fi
            convert_image "$tmp_file" &
        fi
    done
fi
