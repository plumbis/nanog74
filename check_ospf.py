import json
import subprocess



my_command = ["net", "show", "ospf", "neighbor", "json"]

# Run the command
process = subprocess.Popen(my_command, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

# Get the output from the OS
stdout, stderr = process.communicate()
if stderr:
    exit(1)

json_output = json.loads(stdout)
# We expect JSON output starting with {, if that isn't there, something's wrong.
print "Our Output is:"
print json_output["neighbors"]