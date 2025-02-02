# LaPredict/ISSTA21-JIT-DP
> The ISSTA21-JIT-DP (LaPredict) paper and code can be found here: https://github.com/ZZR0/ISSTA21-JIT-DP

This setup makes running LaPpredict replication package easier, by providing a docker image with all required dependencies preinstalled to prevent version conflicts. Code and data are mounted into the container via docker-compose.

## Run the application
### Prerequisites
The setup assumes you have a running docker installation with GPU support.
Specifically:
- docker
- cuda
- docker-nvidia-toolkit

This article might be helpful: [Nvidia Docker on WSL2](https://medium.com/htc-research-engineering-blog/nvidia-docker-on-wsl2-f891dfe34ab)

### Setup
1. The image already constains the original dataset. If you want to extract new data, make sure to mount the respective git-repository from the `repositories` folder to `/home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/git_datasets/`. You can see examples in `docker/docker-compose.yml`.
2. Start the container from the **root** folder (`tools/lapredict`) via: 
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
   docker exec -it lapredict zsh
   ```
2. Now you can run LaPredict. Please refer to their documentation for further details: [https://github.com/ZZR0/ISSTA21-JIT-DP](https://github.com/ZZR0/ISSTA21-JIT-DP)

> **Note**: Since the docker-container will use the GPU of the host system, a different version of pytorch might have to be installed.
> For running on a K40 for example do the following inside the container:
> ```
> pip install torch==1.13.1+cu116 -f https://nelsonliu.me/files/pytorch/whl/torch_stable.html
>
> apt-get update && apt-get install libpython3.7 -y
> ```


### Cleaning up
#### Stopping and removing the container
```bash
docker rm -f lapredict
```
#### Removing the image
```bash
docker image rm lapredict
```

## Build a new image
Build a new docker image from the **root** folder (`tools/lapredict`)! 
````bash
docker build -t lapredict -f docker/Dockerfile .
````