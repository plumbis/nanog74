import json
import subprocess
import paramiko

def ssh_command(host, command):
    """SSH to a host and run a command. Returns json command output
    """
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy)

        client.connect(host, port=22, username="cumulus", password="CumulusLinux!")

        stdin, stdout, stderr = client.exec_command(command)
        return json.loads(stdout.read())

    finally:
        client.close()

def run_command(command):
    """Run a single command on the localhost"""

    # Run the command
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    # Get the output from the OS
    stdout, stderr = process.communicate()
    if stderr:
        exit(1)

    return json.loads(stdout)

def get_ospf_interfaces(host):
    """Get the list of OSPF enabled interfaces from a given host
    """
    command = "net show ospf interface json"

    output = ssh_command(host, command)

    if "interfaces" not in output:
        print 'Error'
        exit(1)
    else:
        return output["interfaces"].keys()

def get_lldp_neighbors(host):
    """Get a list of the lldp peers that are connected
    """
    command = "net show lldp json"

    output = ssh_command(host, command)

    if "lldp" not in output:
        print "Error"
        exit(1)
    else:
        return output

def get_topology():
    """Opens an ansible host file and returns the hostnames
    """
    file_object  = open("ansible.hosts", "r")
    hostnames = []
    for line in file_object.readlines():
        if line.find("[") >= 0 or len(line.strip()) == 0:
            continue
        hostnames.append(line.strip())

    return hostnames

def check_link_status():
    _json_all_port = run_command("net show interface json")
    _correct = True
    for _port in _json_all_port:
        _correct = _correct and (_port["linkstate"] == 'UP')
    return _correct

def check_mtu():
    pass

def check_lldp():
    pass

def check_ospf_state():
    pass

def check_routes():
    pass

def check_expected_spf():
    pass

def check_ospf_calc():
    pass


hostnames = get_topology()
for host in hostnames:
    check_link_status()