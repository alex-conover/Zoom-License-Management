import json
import requests
import subprocess
import sys

##### OAUTH TOKEN CREATION #####
authorize_url = "https://zoom.us/oauth/authorize"
token_url = "https://zoom.us/oauth/token"
callback_uri = "<< ENTER CALLBACK URI HERE >>" #Must match callback uri in Zoom Marketplace App

#   *** EDIT CREDENTIALS HERE: ***
client_id = '<< ENTER CLIENT ID HERE >>'
client_secret = '<< ENTER CLIENT SECTET HERE >>'

authorization_redirect_url = authorize_url + '?response_type=code&client_id=' + client_id + '&redirect_uri=' + callback_uri + '&scope=openid'
#   *** REDIRECT URL & INPUT OF CODE ***
print("go to the following url on the browser and enter the code from the returned url: ")
print("---  " + authorization_redirect_url + "  ---")
authorization_code = input('code: ')
data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': callback_uri}
access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(client_id, client_secret))

#   *** TOKEN ***
tokens = json.loads(access_token_response.text)
access_token = tokens['access_token']
Auth = "Bearer " + access_token 

##### EDIT DATES OF INACTIVE REPORT #####
startDate = "2020-03-01" #<--- EDIT THIS: From date of inactive report (YYYY-MM-DD)
endDate = "2020-04-06" #<--- EDIT THIS: To date of inactive report (YYYY-MM-DD)
dateFilter = 20200301000000 # <--- EDIT THIS: ***Best to set to the same date as the startDate*** This filter sets a date for users that were recently created so they are not set to basic (YYYYMMDDhhmmss)

##### EDIT PARAMS OF INACTIVE REPORT #####
pageSize = "300" # 300 entries is the max page size
pageNum = "1" # <--- # Initial page value
licenseType = "1" # <--- EDIT THIS: To select what to set the users license type to (1 = Basic 2 = Licensed)
loginType = "" # <---- EDIT THIS: To select which login type a user is setup for (ANY = "" SSO - "101", EMAIL - "100", Google - "1" )

#####  API URLS #####
getURL = "https://api.zoom.us/v2/report/users?type=inactive&from=" + startDate + "&to=" + endDate + "&page_size=" + pageSize + "&page_number=" + pageNum #Report URL with page  info

##### GLOBAL LISTS #####
inactiveUsers = []

##### API REQUEST PARAMETER VARIABLES #####
getHeader = {'Authorization': Auth}
getPayload = {}
patchHeader = {'Content-Type': 'application/json','Authorization': Auth}
patchPayload  = "{\n  \"type\": " + '"'+ licenseType + '"' + "\n}"

response = requests.request("GET", getURL, headers=getHeader, data = getPayload)
responseGet = response.json()

pageNumber = str(responseGet['page_number'])
pageCount = str(responseGet['page_count'])
pageCountRange = range(1, (int(pageCount)+1))

#Gets emails from inactive report if they are licensed users, then checks if the user was recently created and adds matches to global list
def inactiveList():
    paidInactiveUsers = []
    print("Checking pages for users to update...")
    for pageNumberIndex in pageCountRange:
        pageNum = str(pageNumberIndex)
        getURL = "https://api.zoom.us/v2/report/users?type=inactive&from=" + startDate + "&to=" + endDate + "&page_size=" + pageSize + "&page_number=" + pageNum #Report URL with page  info
        print(getURL)
        responseGet = requests.request("GET", getURL, headers=getHeader, data = getPayload)
        responseGet = responseGet.json()
        temp = []
        for user in responseGet['users']:
            createTime_Str = user['create_time']
            createTime_Str = createTime_Str.replace("-", "")
            createTime_Str = createTime_Str.replace("T", "")
            createTime_Str = createTime_Str.replace(":", "")
            createTime_Str = createTime_Str.replace("Z", "")
            createTime_Int = int(createTime_Str)
            if user['type'] == 2 and createTime_Int < dateFilter:
                temp.append(user['email'])
        paidInactiveUsers.extend(temp)
        print("Users matching filters on page: " + str(len(temp)))
    return paidInactiveUsers
   
inactiveUsers = inactiveList()

#Sets PATCH API string to users email from list of inactive users 
def updateUrlList(i):
    updateURLs = []
    for i, email in enumerate(inactiveUsers): 
        updateURLs.append("https://api.zoom.us/v2/" + "users/" + email + "?login_type=" + loginType)
    return(updateURLs)

updateURL = updateUrlList(inactiveUsers)
print("Number of users to be updated: " + str(len(updateURL)))

for i , updateURL in enumerate(updateURL):
    response = requests.request("PATCH", updateURL, headers=patchHeader, data = patchPayload)
    response = response.text
    if response == "":
        email = updateURL.replace("https://api.zoom.us/v2/users/", "")
        email = email.replace("?login_type=", "")
        print(email + " has been set to Basic")
    else:
        print(email + " has failed to update - Error: " + response)