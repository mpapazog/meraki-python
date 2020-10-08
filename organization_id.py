read_me = '''This is a Python 3 script to print your organizationId for a given name. Usage
'''

import sys, getopt, requests, time, datetime

#SECTION: GLOBAL VARIABLES: MODIFY TO CHANGE SCRIPT BEHAVIOUR

API_EXEC_DELAY              = 0.21 #Used in merakiRequestThrottler() to avoid hitting dashboard API max request rate

#connect and read timeouts for the Requests module in seconds
REQUESTS_CONNECT_TIMEOUT    = 90
REQUESTS_READ_TIMEOUT       = 90

#SECTION: GLOBAL VARIABLES AND CLASSES: DO NOT MODIFY

LAST_MERAKI_REQUEST         = datetime.datetime.now()   #used by merakiRequestThrottler()
API_BASE_URL                = 'https://api-mp.meraki.com/api/v0'
API_BASE_URL_MEGA_PROXY     = 'https://api-mp.meraki.com/api/v0'
API_BASE_URL_NO_MEGA        = 'https://api.meraki.com/api/v0'


### SECTION: General functions


def printHelpAndExit():
    print(read_me)
    sys.exit(0)
       
        
### SECTION: Functions for interacting with Dashboard       


def merakiRequestThrottler():
    #prevents hitting max request rate shaper of the Meraki Dashboard API
    global LAST_MERAKI_REQUEST
    
    if (datetime.datetime.now()-LAST_MERAKI_REQUEST).total_seconds() < (API_EXEC_DELAY):
        time.sleep(API_EXEC_DELAY)
    
    LAST_MERAKI_REQUEST = datetime.datetime.now()
    return
    
        
def getOrgId(p_apiKey, p_orgName):
    #returns the organizations' list for a specified admin, with filters applied
        
    merakiRequestThrottler()
    try:
        r = requests.get( API_BASE_URL + '/organizations', headers={'X-Cisco-Meraki-API-Key': p_apiKey, 'Content-Type': 'application/json'}, timeout=(REQUESTS_CONNECT_TIMEOUT, REQUESTS_READ_TIMEOUT) )
    except:
        return None
    
    if r.status_code != requests.codes.ok:
        return None
        
    rjson = r.json()
    
    for org in rjson:
        if org['name'] == p_orgName:
            return org['id']
    
    return None
  
### SECTION: Main function    

  
def main(argv):
    global API_BASE_URL
    
    #set default values for command line arguments
    arg_apikey      = None
    arg_orgname     = None
        
    try:
        opts, args = getopt.getopt(argv, 'hk:o:')
    except getopt.GetoptError:
        printHelpAndExit()
    
    for opt, arg in opts:
        if opt == '-h':
            printHelpAndExit()
        elif opt == '-k':
            arg_apikey = arg
        elif opt == '-o':
            arg_orgname = arg
                
    #check if all required parameters have been given
    if arg_apikey is None or arg_orgname is None:
        printHelpAndExit()
        
    API_BASE_URL = API_BASE_URL_MEGA_PROXY            
                        
    #get organization id corresponding to org name provided by user
    orgId = getOrgId(arg_apikey, arg_orgname)
    if orgId is None:
        print('ERROR 16: Fetching organization id failed')
        sys.exit(2)
    
    print(orgId)
                     
if __name__ == '__main__':
    main(sys.argv[1:])
