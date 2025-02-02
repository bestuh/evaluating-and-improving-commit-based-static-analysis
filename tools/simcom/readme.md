# SimCom
> The SimCom paper can be found here: https://ieeexplore.ieee.org/document/9796345 
> The SimCom code can be found here: https://github.com/soarsmu/SimCom_JIT

This setup makes running SimCom easier, by providing a docker image with all required dependencies preinstalled to prevent version conflicts. The image itself does not contain the SimCom code or data. Instead it is mounted into the container via docker-compose.

## Run the application
### Prerequisites
The setup assumes you have a running docker installation with GPU support.
Specifically:
- docker
- cuda
- docker-nvidia-toolkit

This article might be helpful: [Nvidia Docker on WSL2](https://medium.com/htc-research-engineering-blog/nvidia-docker-on-wsl2-f891dfe34ab)

### Setup
1. Download the SimCom data from https://drive.google.com/file/d/1WbWC2lhHLW16OCycV4yLzIF9S4dLb6om/view. Put it into `code/data`.
2. Start the container from the **root** folder (`tools/simcom`) via: 
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    ```
3. You can stop it again by running the following command:
    ```bash
    docker-compose -f docker/docker-compose.yml down
    ```

## Usage
1. You can now attach to the container via:
   ```bash
   docker exec -it simcom bash
   ```
2. Now you can run SimCom. Please refer to their documentation for further details: [https://github.com/soarsmu/SimCom_JIT](https://github.com/soarsmu/SimCom_JIT) 

### Cleaning up
#### Stopping and removing the container
```bash
docker rm -f simcom
```
#### Removing the image
```bash
docker image rm simcom
```

## Build a new image
Build a new docker image from the **root** folder (`tools/simcom`)! 
````bash
docker build -t simcom -f docker/Dockerfile .
````