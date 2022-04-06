import subprocess
import json
import time
from functools import reduce
import operator

def lab3():
    return ["cs19%.3dbs" %i for i in range(90,120)]

machines = lab3()

def free_row(machine):
    users_string = ""
    for user in machine["users_details"]:
        if user["idle"]:
            users_string += "<i>%s</i>, " %user["username"]
        else:
            users_string += "<b>%s</b>, " %user["username"]
    return '<tr class="table-success">\
<td>%s</td>\
<td>%s</td>\
<td>%d%% (%d%%)</td>\
<td>%d%% (%d%%)</td></tr>\n' %(machine["hostname"], users_string, machine["cpu"], machine["cpu_avg"], machine["gpu"], machine["gpu_avg"])


def inuse_row(machine):
    users_string = ""
    for user in machine["users_details"]:
        if user["idle"]:
            users_string += "<i>%s</i>, " %user["username"]
        else:
            users_string += "<b>%s</b>, " %user["username"]
    return '<tr class="table-warning">\
<td>%s</td>\
<td>%s</td>\
<td>%d%% (%d%%)</td>\
<td>%d%% (%d%%)</td></tr>\n' %(machine["hostname"], users_string, machine["cpu"], machine["cpu_avg"], machine["gpu"], machine["gpu_avg"])

def offline_row(machine):
    return '<tr class="table-danger">\
<td>%s - OFFLINE</td>\
<td>-</td>\
<td>-</td>\
<td>-</td></tr>\n' % machine["hostname"]

def build_page(statuses):
    page = ""
    with open("/home/cosc/guest/jmm403/Projects/monitor/head.html", "r") as head:
        page += head.read()


    for hostname in machines:
        #machine = get_machine(hostname)
        machine = statuses[hostname]
        #print(machine)
        machine["hostname"]= hostname

        activity = 0
        if len(machine["users_details"]) > 0:
            activity = reduce(operator.add,  map(lambda e: 0 if e["idle"] else 1, machine["users_details"]))

        if machine["online"] and activity == 0:
            page += free_row(machine)
        elif machine["online"]:
            page += inuse_row(machine)
        else:
            page += offline_row(machine)

    with open("/home/cosc/guest/jmm403/Projects/monitor/tail.html", "r") as tail:
        page += tail.read()

    with open("/home/cosc/guest/jmm403/Projects/monitor/index.html", "w") as index:
        index.write(page)

def build_json(status):
    status = {"machines": status, "unix_time": time.time()}
    with open("/home/cosc/guest/jmm403/Projects/monitor/status.json",'w') as status_file:
        status_file.write(json.dumps(status, sort_keys=True, indent=4))


def get_machine(host):
    subp = subprocess.run(["ssh", host, "-o","ConnectTimeout=2", "-o","BatchMode=yes", "-o","UserKnownHostsFile=/dev/null", "-o","StrictHostKeyChecking=no", "python3", "~/Projects/monitor/client.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if subp.returncode != 0:
        return {"users":[], "users_details": [], "gpu": 0, "cpu": 0, "gpu_avg": 0, "cpu_avg": 0, "online": False}
    else:
        stdout = subp.stdout.decode("utf8").strip()
        return json.loads(stdout)

def get_machines_statuses():
    statuses = dict()
    for hostname in machines:
        status = get_machine(hostname)
        statuses[hostname] = status
    return statuses


def push():
    subprocess.run(["scp","/home/cosc/guest/jmm403/Projects/monitor/index.html","root@joshm.cc:/var/www/labs.joshm.cc/index.html"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["scp","/home/cosc/guest/jmm403/Projects/monitor/status.json","root@joshm.cc:/var/www/labs.joshm.cc/status.json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

statuses = get_machines_statuses()
build_json(statuses)
build_page(statuses)
push()

