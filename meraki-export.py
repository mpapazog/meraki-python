#!/usr/bin/env python3
# Before running this script you need to install these three modules:
# pip install meraki yaml argparse
from meraki import meraki
import argparse
import yaml

config={} #Define config as a dictionary
config["Organization"]={} #Define organization as a dictionary
config["Organization"]["Network"]=[] #but Network is a list
def get_org_id(apikey,orgName,suppressprint): #Turns an org name into an org ID
    result = meraki.myorgaccess(apikey, suppressprint)
    for row in result:
        if row['name'] == orgName:
            return row['id']

    raise ValueError('The organization name does not exist')

def admins(apikey, orgid, suppressprint): # Retrieves a list of admins
    myOrgAdmins=meraki.getorgadmins(apikey, orgid, suppressprint)
    config["Organization"]["Admins"]=myOrgAdmins
    print("Got admins")

def mx_l3_fw_rules(apikey,networkid,suppressprint): #Retrieves the Layer 3 firewall rules on the MX
    myRules=meraki.getmxl3fwrules(apikey, networkid, suppressprint)[0:-1]
    network["L3-Firewall-Rules"]=myRules
    print("Got Layer 3 firewall rules")

def mx_cellular_fw_rules(apikey,networkid,suppressprint): # Retrieves the mobile firewall rules
    myRules=meraki.getmxcellularfwrules(apikey, networkid, suppressprint)[0:-1]
    network["Cell-Firewall-Rules"]=myRules
    print("Got mobile firewall rules")

def mx_vpn_fw_rules(apikey,orgid,suppressprint): # Retrieves the VPN firewall rules
    myRules=meraki.getmxvpnfwrules(apikey, orgid, suppressprint)[0:-1]
    config["Organization"]["MX-VPN-Firewall-Rules"]=myRules
    print("Got VPN firewall rules")

def vpn_settings(apikey,networkid,suppressprint): # Retrieves Meraki S2S VPN settings
    myVPN=meraki.getvpnsettings(apikey, networkid, suppressprint)
    network["VPN-Settings"]=myVPN
    print("Got VPN settings")

def snmp_settings(apikey,orgid,suppressprint): # Retrieves SNMP settings
    mySNMP=meraki.getsnmpsettings(apikey, orgid, suppressprint)
    config["Organization"]["SNMP"]=mySNMP
    print("Got SNMP settings")

def non_meraki_vpn_peers(apikey,orgid,suppressprint): # Retrieves non-Meraki site-to-site
    myPeers=meraki.getnonmerakivpnpeers(apikey,orgid,suppressprint)
    config["Organization"]["Non-Meraki-VPN"]=myPeers
    print("Got non-Meraki VPN peers")

def static_routes(apikey,networkid,suppressprint): # Retrieve any static routes
    myRoutes=meraki.getstaticroutes(apikey,networkid,suppressprint)
    if myRoutes is None:
        return
    network["Routes"]=myRoutes
    print("Got static routes")

def ssid_settings(apikey,networkid,suppressprint): # Retrieve all SSID settings
    mySSIDs=meraki.getssids(apikey, networkid, suppressprint)
    if mySSIDs is None:
        return
    for row in mySSIDs:
        myRules=meraki.getssidl3fwrules(apikey, networkid, row['number'], suppressprint)[0:-2]
        row["rules"]=myRules
        network["SSID"].append(row)
        print("Got SSID "+str(row["number"]))
####################################################
# Main program
# ##################################################    
parser = argparse.ArgumentParser(description='Backup a Meraki config to an offline file.')
parser.add_argument('-v', help='Enable verbose mode',action='store_true')
parser.add_argument('apiKey', help='The API Key')
parser.add_argument('orgName', help='The name of a Meraki organisation')
args = parser.parse_args() # Defines arguments passed on the command line when running program

suppressprint=True
if args.v:
    suppressprint=False

apikey=args.apiKey
orgid=get_org_id(apikey,args.orgName,suppressprint) 
file="%s.yml"%args.orgName # set the filename from the network name
config["Organization"]["Name"]=args.orgName
config["Organization"]["ID"]=orgid
admins(apikey, orgid, suppressprint)
mx_vpn_fw_rules(apikey,orgid,suppressprint)
snmp_settings(apikey,orgid,suppressprint)
non_meraki_vpn_peers(apikey,orgid,suppressprint)    
myNetworks = meraki.getnetworklist(apikey, orgid, None, suppressprint)
for row in myNetworks: # Iterate through the networks in the org
    tags=row['tags']
    if tags == None:
        tags = ""
    networkType=row['type']
    if networkType == 'combined': # Combined is not valid to upload!
        networkType = 'wireless switch appliance phone'
    if networkType == 'systems manager': # We don't care about MDM networks
        continue
    print("Processing network "+row['name'])
    network={"name": row["name"], "networkType": networkType, "tags": tags, "timeZone":row["timeZone"]}
    mx_cellular_fw_rules(apikey,row['id'],suppressprint)
    mx_l3_fw_rules(apikey,row['id'],suppressprint)
    vpn_settings(apikey,row['id'],suppressprint)
    static_routes(apikey,row["id"],suppressprint)
    network["SSID"]=[]
    ssid_settings(apikey,row['id'],suppressprint)
    config["Organization"]["Network"].append(network)
with open(file, 'w') as file: # open the file we defined earlier to write to
    file.write("---\n")
    file.write(yaml.dump(config)) # convert the config dict to yaml and save
    file.flush()
    file.close()