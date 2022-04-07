import subprocess
import json
import time
from functools import reduce
import operator
import os
from urllib.parse import quote_plus

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

def build_table(lab, statuses):
    table_string = ""
    for hostname in lab["machines"]:
        machine = statuses[hostname]
        machine["hostname"] = hostname

        activity = 0
        if len(machine["users_details"]) > 0:
            activity = reduce(operator.add,  map(lambda e: 0 if e["idle"] else 1, machine["users_details"]))

        if machine["online"] and activity == 0:
            table_string += free_row(machine)
        elif machine["online"]:
            table_string += inuse_row(machine)
        else:
            table_string += offline_row(machine)

    with open("/home/cosc/guest/jmm403/Projects/monitor/table.template", "r") as table_template:
        return table_template.read().format(
            lab_name=lab["name"],
            json_filename=quote_plus(lab["name"]+".json"),
            table_rows=table_string)


def build_json(status, filename):
    status = {"machines": status, "unix_time": time.time()}
    with open(filename,'w') as status_file:
        status_file.write(json.dumps(status, sort_keys=True, indent=4))


def get_machine(host):
    subp = subprocess.run(["ssh", host, "-o","ConnectTimeout=2", "-o","BatchMode=yes", "-o","UserKnownHostsFile=/dev/null", "-o","StrictHostKeyChecking=no", "python3", "~/Projects/monitor/client.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if subp.returncode != 0:
        return {"users":[], "users_details": [], "gpu": 0, "cpu": 0, "gpu_avg": 0, "cpu_avg": 0, "online": False}
    else:
        stdout = subp.stdout.decode("utf8").strip()
        return json.loads(stdout)

def get_machines_statuses(machines):
    statuses = dict()
    for hostname in machines:
        status = get_machine(hostname)
        statuses[hostname] = status
    return statuses


def push(filename, remote, ):
    subprocess.run(["scp",
        filename,
        remote+os.path.basename(filename)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":

    working_dir = os.path.dirname(__file__)
    with open(os.path.join(working_dir,"config.json")) as config_file:
        config = json.loads(config_file.read())

    tables = ""
    for lab in config["labs"]:
        lab_name = lab["name"]
        lab_name_save = quote_plus(lab_name)
        json_filename = os.path.join(working_dir, f"{lab_name_save}.json")

        statuses = get_machines_statuses(lab["machines"])
        build_json(statuses, json_filename)
        push(json_filename, config["deployment"]["location"])
        tables += build_table(lab,statuses)


    with open(os.path.join(working_dir,"page.template"), "r") as page_template:
        page = page_template.read().format(
            lab_name=lab["name"],
            json_filename=lab["name"]+".json",
            tables=tables)

    with open(os.path.join(working_dir,"index.html"), "w") as page_file:
        page_file.write(page)
    push(os.path.join(working_dir,"index.html"), config["deployment"]["location"])

