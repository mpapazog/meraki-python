# Test YML looks like:
# ---
# NetworkID: Z_9512345678
# API_Key: c1234567890abcdef01234
# Gateway:
#   - GW: "1.2.3.4"
#     Networks:
#     - Network: "10.1.1.0/24"
#       Name: "Net 10.1.1.0-24"
#     - Network: "10.1.2.0/24"
#       Name: "Net 10.1.2.0-24"
#   - GW: "2.3.4.5"
#     Networks:
#     - Network: "10.2.1.0/24"
#       Name: "10.2.1.0-24"
#     - Network: "10.2.2.0/24"
#       Name: "10.2.2.0-24"
import yaml, requests, json
with open ("StaticRoutes.yml") as file1:
    config = yaml.load (file1)
url = "https://dashboard.meraki.com/api/v0/networks/%s/staticRoutes" % config["NetworkID"]
headers = {
    'X-Cisco-Meraki-API-Key': "%s" %config["API_Key"],
    'Content-Type': "application/json",
    'Cache-Control': "no-cache",
    }
for gateway in config["Gateway"]:
    GatewayIP=gateway["GW"]
    for network in gateway["Networks"]:
        payload = {
            "name" : network["Name"],
            "subnet": network["Network"],
            "gatewayIp": gateway["GW"],
            "enabled":"true"
        }
        response = requests.request("POST", url, data=json.dumps(payload), headers=headers)
        print(response.status_code, response.text)