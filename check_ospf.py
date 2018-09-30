import json
import subprocess
import paramiko

def print_error(error_string):
    """Format and print error messages.
    Also exit the program
    """
    error_format = "\033[91m"
    bold_format = "\033[1m"
    endc = '\033[0m'
    print error_format + bold_format + error_string + endc

def print_green(output_string):
    """Print a string in green
    """
    green_format = "\033[92m"
    endc = '\033[0m'
    print green_format + output_string + endc

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
    except:
        print "Could not connect to " + host
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

def check_link_status(hostname):
    """ Traverse every port and return if ok on all port
    """
    _json_all_port = ssh_command(hostname, "net show interface json")
    _correct = True
    for _remote_port in _json_all_port:
        _correct = _correct and (_json_all_port[_remote_port]['linkstate'] == 'UP')
        if _json_all_port[_remote_port]['linkstate'] != 'UP':
            print_error("Link failed on " + hostname +
                        " with remote port : " + _remote_port + "\n")
    if _correct:
        print_green("...Link status passed")
    return _correct

def check_mtu(host_dict):
    print "Checking MTU...."
    for host in host_dict.keys():
        for interface in get_lldp_neighbors(host)["lldp"][0]["interface"]:
            # print "local host: " + host
            # print "local port: " + interface["name"]
            # print "remote host: " + interface["chassis"][0]["name"][0]["value"]
            # print "remote port: " + interface["port"][0]["id"][0]["value"]
            # exit(1)
            """
            host_dict["leaf01"] =
                {"interfaces":
                    {"swp51":
                        {"spine01": "swp1"}
                    },
                    {"swp52":
                        {"spine02": "swp2}
                    }
                }
            """
            host_dict[host]["interfaces"].update(
                {interface["name"]:
                    {interface["chassis"][0]["name"][0]["value"]:
                        interface["port"][0]["id"][0]["value"]}})

    for host in host_dict:
        for interface in host_dict[host]["interfaces"]:
            my_mtu = ssh_command(host, "net show interface " + interface + " json")["iface_obj"]["mtu"]
            peer = host_dict[host]["interfaces"][interface]
            remote_host = peer.keys()[0]
            remote_port = host_dict[host]["interfaces"][interface][remote_host]
            remote_mtu = ssh_command(remote_host, "net show interface " + remote_port + " json")["iface_obj"]["mtu"]

            if not remote_mtu == my_mtu:
                print_error("...MTU check failed")
                print_error("MTU mismatch on " + host + ":" + interface + \
                    "(" + str(my_mtu) + ") and " + remote_host + \
                      ":" + remote_port + "(" + str(remote_mtu) + ")")
                return False

    print_green("...MTU check passed")
    return True

def check_ospf_state():
    interfaces = run_command("net show interface json")
    for interface_name, interface_data in interfaces.iteritems():
        if interface_data['mode'] == 'Interface/L3' and 'swp' in interface_name:
            ospf_state = run_command("net show ospf neighbor json")
            for neighbor_ip, neighbors in ospf_state['neighbors'].iteritems():
                for neighbor_data in neighbors:
                    if interface_name in neighbor_data['ifaceName']:
                        print "Interface %s OSPF state is %s" % (interface_name, neighbor_data['state'])

def check_network_type(hostname):
    ifc_info = ssh_command(hostname, "net show ospf interface json")

    for (k, v) in ifc_info.items():
        for (ifc, ifc_v) in v.items():
            for(attr, attr_v) in ifc_v.items():
                if(ifc != "lo" and attr == "networkType"):
                    #print("ifc: "+ ifc + " Key: " + attr +  " Value:" + str(attr_v))
                    if(attr_v != "POINTOPOINT"):
                        print_error("...failed")
                        print_error(hostname + ":" + v + " configured as " + attr_v)
                        return False
                    else:
                        print_green("...OSPF network type checking passed")
                        return True

def check_ospf_routerid(hostnames):
    """ Using the topology host list to check if they have same id
    """
    _unique_id = {}
    _command = "net show ospf json"
    _correct = True;
    for host in hostnames:
        _ospf_info = ssh_command(host, _command)
        _ospf_id = _ospf_info['routerId']
        if _ospf_id not in _unique_id :
            _unique_id[_ospf_id] = [host]
        else:
            _unique_id[_ospf_id].append(host)

    for id in _unique_id:
        if _unique_id[id].amount() > 1:
            _correct = False
            print("Repetitive Unique ID :" + id + "with host name :" )
            for id_host in _unique_id[id]:
                print(id_host)
            print ("\n")

    return _correct





all_passed = True
host_dict = dict()
hostnames = get_topology()
for host in hostnames:
    host_dict[host] = {"interfaces": dict()}
    print "Checking interface status..."
    if not check_link_status(host):
        all_passed = False
    print ""
    print "Checking OSPF network type..."
    if not check_network_type(host):
        all_passed = False
    print ""

if not check_ospf_routerid(hostnames):
    all_passed = False
if not check_mtu(host_dict):
    all_passed = False

print ""
if all_passed:
    print_green("All Checks Pass")
else:
    exit(1)