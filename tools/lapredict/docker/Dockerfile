FROM zzr0/issta2021-jit-dp:v1.0

WORKDIR /home/jit-dp/ISSTA21-JIT-DP
# delete those files so docker-compose works correctly with GPU support
RUN rm -rf /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 /usr/lib/x86_64-linux-gnu/libcuda.so.1
# for some reason some requirements are not installed in the original image
RUN /root/.pyenv/shims/pip install -r requirements.txt
# start the mongodb
ENTRYPOINT ["mongod --fork --syslog"]