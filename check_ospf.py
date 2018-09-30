import json
import subprocess
import paramiko

def ssh_command(host, command):
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

    # Run the command
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    # Get the output from the OS
    stdout, stderr = process.communicate()
    if stderr:
        exit(1)

    return json.loads(stdout)

def get_ospf_interfaces(host):
    command = "net show ospf interface json"

    output = ssh_command(host, command)

    if "interfaces" not in output:
        print 'Error'
        exit(1)
    else:
        return output["interfaces"].keys()

def check_link_status():
    pass

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
