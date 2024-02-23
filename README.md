# Dockerized Image Converter to WebP

This project provides a Dockerized solution for converting images to the WebP format, leveraging ImageMagick for image processing. It is designed to monitor a directory for new images, automatically convert them to WebP format with optimized size and quality, and handle image processing errors gracefully.

## Features

- **Automatic Conversion:** Watches for new images in the input directory and converts them to WebP format.
- **Error Handling:** Moves problematic images to an error directory and logs errors for troubleshooting.
- **Success Logging:** Logs details about each successful conversion, including file size reduction percentages.
- **Cleanup on Exit:** Cleans up error and log directories upon Docker container shutdown.

## Prerequisites

- Docker

## Setup

1. **Build the Docker Image**

   Clone this repository and navigate to the project directory. Build the Docker image using the following command:

   ```sh
   docker build -t image-to-webp .
   ```

2. **Run the Docker Container**

   Start the container with the following command:

   ```sh
   docker run -d \
     --name image-converter \
     -v ./input:/app/input \
     -v ./output:/app/output \
     -v ./tmp:/app/tmp \
     -v ./error:/app/error \
     -v ./log:/app/log \
     image-to-webp
   ```

  For a quick start you may also use the provided docker-compose.yml file. To get the container running using the docker-compose.yml run:
  ```sh
   docker compose up -d 
  ```

## Usage

Place any images you want to convert into the input directory. The script will automatically convert them to WebP format and place them in the output directory. Errors and logs are managed internally within the container, but you can attach to the container's log to monitor the process:

```sh
docker logs -f image-converter
```

## Customization

You can customize the behavior of the image conversion (e.g., resize dimensions, quality) by modifying the `convert_to_webp.sh` script. After making your changes, rebuild the Docker image for them to take effect.

## Cleanup

The Docker container is configured to clean up error logs and problematic images upon shutdown. If you need to manually clean these files, stop the container and then start it again.

## Contributing

Contributions to this project are welcome. Please fork the repository, make your changes, and submit a pull request.

## License

This project is open-sourced under the MIT License. See the LICENSE file for more details.
