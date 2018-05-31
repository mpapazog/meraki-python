#!/usr/bin/env python3
#
# Before running this script you need to install these two modules:
# pip install requests
# pip install meraki
#
from meraki import meraki
import argparse
import yaml

config={}
config["Organization"]={}
config["Organization"]["Network"]={}
def get_org_id(apikey,orgName,suppressprint):
    result = meraki.myorgaccess(apikey, suppressprint)
    for row in result:
        if row['name'] == orgName:
            return row['id']

    raise ValueError('The organization name does not exist')

def admins(apikey, orgid, suppressprint):
    myOrgAdmins=meraki.getorgadmins(apikey, orgid, suppressprint)
    config["Organization"]["Admins"]=myOrgAdmins
    print("Got admins")

def mx_l3_fw_rules(apikey,networkid,suppressprint):
    myRules=meraki.getmxl3fwrules(apikey, networkid, suppressprint)[0:-1]
    network["L3-Firewall-Rules"]=myRules
    print("Got Layer 3 firewall rules")

def mx_cellular_fw_rules(apikey,networkid,suppressprint):
    myRules=meraki.getmxcellularfwrules(apikey, networkid, suppressprint)[0:-1]
    network["Cell-Firewall-Rules"]=myRules
    print("Got mobile firewall rules")

def mx_vpn_fw_rules(apikey,orgid,suppressprint):
    myRules=meraki.getmxvpnfwrules(apikey, orgid, suppressprint)[0:-1]
    config["Organization"]["MX-VPN-Firewall-Rules"]=myRules
    print("Got VPN firewall rules")

def vpn_settings(apikey,networkid,suppressprint):
    myVPN=meraki.getvpnsettings(apikey, networkid, suppressprint)
    network["VPN-Settings"]=myVPN
    print("Got VPN settings")

def snmp_settings(apikey,orgid,suppressprint):
    mySNMP=meraki.getsnmpsettings(apikey, orgid, suppressprint)
    if 'v2CommunityString' in mySNMP:
        del mySNMP['v2CommunityString']
    if 'hostname' in mySNMP:
        del mySNMP['hostname']
    if 'port' in mySNMP:
        del mySNMP['port']
    config["Organization"]["SNMP"]=mySNMP
    print("Got SNMP settings")

def non_meraki_vpn_peers(apikey,orgid,suppressprint):
    myPeers=meraki.getnonmerakivpnpeers(apikey,orgid,suppressprint)
    config["Organization"]["Non-Meraki-VPN"]=myPeers
    print("Got non-Meraki VPN peers")

def static_routes(apikey,networkid,suppressprint):
    myRoutes=meraki.getstaticroutes(apikey,networkid,suppressprint)
    if myRoutes is None:
        return
    network["Routes"]=myRoutes
    print("Got static routes")

def ssid_settings(apikey,networkid,suppressprint):
    mySSIDs=meraki.getssids(apikey, networkid, suppressprint)
    if mySSIDs is None:
        return
    for row in mySSIDs:
        myRules=meraki.getssidl3fwrules(apikey, networkid, row['number'], suppressprint)[0:-2]
        row["rules"]=myRules
        network["SSID"][row["number"]]=row
        print("Got SSID "+str(row["number"]))
####################################################
# Main program
# ##################################################    
parser = argparse.ArgumentParser(description='Backup a Meraki config to an offline file.')
parser.add_argument('-v', help='Enable verbose mode',action='store_true')
parser.add_argument('apiKey', help='The API Key')
parser.add_argument('orgName', help='The name of a Meraki organisation')
args = parser.parse_args()

suppressprint=True
if args.v:
    suppressprint=False

apikey=args.apiKey
orgid=get_org_id(apikey,args.orgName,suppressprint)
file="%s.yml"%args.orgName
config["Organization"]["Name"]=args.orgName
config["Organization"]["ID"]=orgid
admins(apikey, orgid, suppressprint)
mx_vpn_fw_rules(apikey,orgid,suppressprint)
snmp_settings(apikey,orgid,suppressprint)
non_meraki_vpn_peers(apikey,orgid,suppressprint)    
myNetworks = meraki.getnetworklist(apikey, orgid, None, suppressprint)
for row in myNetworks:
    tags=row['tags']
    if tags == None:
        tags = ""
    networkType=row['type']
    if networkType == 'combined':
        networkType = 'wireless switch appliance phone'
    if networkType == 'systems manager':
        continue
    print("Processing network "+row['name'])
    network={"name": row["name"], "networkType": networkType, "tags": tags, "timeZone":row["timeZone"]}
    mx_cellular_fw_rules(apikey,row['id'],suppressprint)
    mx_l3_fw_rules(apikey,row['id'],suppressprint)
    vpn_settings(apikey,row['id'],suppressprint)
    static_routes(apikey,row["id"],suppressprint)
    network["SSID"]={}
    ssid_settings(apikey,row['id'],suppressprint)
    config["Organization"]["Network"][row["id"]]=network
with open(file, 'w') as file:
    file.write("---\n")
    file.write(yaml.dump(config))
    file.flush()
    file.close()
