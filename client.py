import subprocess
import json
import socket
import os.path

def get_cpu():
    stdout = subprocess.run(["uptime"], stdout=subprocess.PIPE).stdout.decode("utf8").strip().split(" ")
    return [float(i.strip(','))*100 for i in stdout[-3:]]

def get_gpu():
    try:
        stdout = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE).stdout.decode("utf8")
        perf_line = stdout.split('\n')[9]
        return float(perf_line.split()[12].strip('%'))
    except:
        return 999.9

def get_average_gpu():
    current_gpu = get_gpu()
    gpu_avg_filename = "/home/cosc/guest/jmm403/Projects/monitor/gpu_averages/"+socket.gethostname()+".avg"
    try:
        if os.path.isfile(gpu_avg_filename):
            with open(gpu_avg_filename, "r") as gpu_avg_file:
                gpu_avg = float(gpu_avg_file.read())
        else:
            gpu_avg = 0
    except:
        gpu_avg = 0

    ema = 0.3
    new_avg = current_gpu * ema + gpu_avg * (1-ema)
    try:
        with open(gpu_avg_filename, "w") as gpu_avg_file:
            gpu_avg_file.write(str(new_avg))
    except:
        pass
    return new_avg


def users():
    stdout = subprocess.run(["finger"], stdout=subprocess.PIPE).stdout.decode("utf8").strip()
    user_lines = stdout.split('\n')[1:]
    users = list(set([user.split(" ")[0] for user in user_lines]))
    return(users)

def users2():
    stdout = subprocess.run(["who", "-u"], stdout=subprocess.PIPE).stdout.decode("utf8").strip()
    user_lines = stdout.split('\n')
    users = []
    for user in user_lines:
        if len(user) > 10:
            user_name = user[:9].strip()
            user_time = user[40:45].strip()
            user_address = user[45:].strip().split(" ")[1][1:-1]
            users.append({"username": user_name, "idle": user_time == "old", "address": user_address, "local": user_address[0] == ":"})
    users.sort(key=lambda e: 1 if e["idle"] else 0)
    return users


def stats():
    return json.dumps({"users":users(), "users_details": users2(), "gpu": get_gpu(), "gpu_avg": get_average_gpu(), "cpu": get_cpu()[0]/8, "cpu_avg": get_cpu()[2]/8, "online": True})

if __name__ == "__main__":
    print(stats())
