import json
import subprocess


def run_command(command):

    # Run the command
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    # Get the output from the OS
    stdout, stderr = process.communicate()
    if stderr:
        exit(1)

    return json.loads(stdout)

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