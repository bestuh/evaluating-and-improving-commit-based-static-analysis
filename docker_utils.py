import docker

def run_in_docker(container_name, command):
    print(f"Running command in {container_name} container: \"{clean_command(command)}\"")
    print()

    docker_client = docker.from_env()
    container = docker_client.containers.get(container_name)
    _, output = container.exec_run(command, stream=True)
    print_container_output(output)


def print_container_output(output):
    print("################## Start container output ##################")
    for line in output:
        line = line.decode("utf-8")
        if "\r" in line:
            line = line.replace("\r", "")
            print(line, end="\r")
        else:
            print(line)
    print("################## End container output ####################")


def clean_command(command):
    return " ".join(command.split())