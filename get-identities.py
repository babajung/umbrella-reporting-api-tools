import json
import requests
import configparser
import os
import sys

# get channel_secret and channel_access_token from your environment variable
org_id = os.getenv('ORGID', None)
mgmt_api_key = os.getenv('MANAGEMENTAPIKEY', None)
mgmt_api_secret = os.getenv('MANAGEMENTAPISECRET', None)
if org_id is None:
    print('Specify ORGID as environment variable.')
    sys.exit(1)
if mgmt_api_key is None:
    print('Specify MANAGEMENTAPIKEY as environment variable.')
    sys.exit(1)
if mgmt_api_secret is None:
    print('Specify MANAGEMENTAPISECRET as environment variable.')
    sys.exit(1)

# read variables from config
config = configparser.ConfigParser()
config.read('config')
#org_id = config['Umbrella']['OrgID']
#mgmt_api_key = config['Umbrella']['ManagementAPIKey']
#mgmt_api_secret = config['Umbrella']['ManagementAPISecret']

search_type = config['SearchOptions']['Type']
category_type = config['SearchOptions']['Category']
application_name = config['SearchOptions']['Application']

header = {'content-type': 'application/json'}

# management api url, used to get access token for reporting api
mgmt_api_url = 'https://management.api.umbrella.com/auth/v2/oauth2/token'

# reporting api url
reporting_api_url = 'https://reports.api.umbrella.com/v2'

def get_reporting_request(access_token, endpoint):
    header['Authorization'] = 'Bearer {}'.format(access_token)
    r = requests.get(reporting_api_url+endpoint, headers=header, allow_redirects=False)
    if r.status_code == 302:
        url_redirect = r.headers['Location']
        print("REDIRECT to {}\n..\n".format(url_redirect))
        r = requests.get(url_redirect, headers=header, allow_redirects=False)
    body = json.loads(r.content)
    return body

def get_access_token():
    r = requests.get(mgmt_api_url, headers=header, auth=(mgmt_api_key, mgmt_api_secret))
    body = json.loads(r.content)
    return body['access_token']


if __name__ == '__main__':

    if search_type.lower() == 'category':
        search_param = category_type
        list_endpoint = 'categories'
        type_param = 'categories'
        error_text = 'category type'
    elif search_type.lower() == 'application':
        search_param = application_name
        list_endpoint = 'applications'
        type_param = 'applicationid'
        error_text = 'application name'
    else:
        print('\nError, unknown search type "{}" in config file. Use either "Category" or "Application".'.format(search_type))
        exit(1)

    # get access token
    access_token = get_access_token()

    # get list of all categories or applications
    r = get_reporting_request(access_token, '/organizations/{}/{}'.format(org_id, list_endpoint))

    # loop througth categories or applications list and get id
    search_id = ''
    for i in r['data'][list_endpoint]:
        if 'label' in i:
            if i['label'].lower() == search_param.lower():
                search_id = i['id']
                break

    if search_id == '':
        print('\nError, unknown {}, "{}" in config file.'.format(error_text, search_param))
        exit(1)

    # get identities for specific category or application
    r = get_reporting_request(access_token, '/organizations/{}/top-identities?from=-30days&to=now&limit=1000&offset=0&{}={}'.format(org_id, type_param, search_id))

    # format row for printing in columns
    row_format = '{:50} {:20} {}'
    print('')
    print(row_format.format('Identity', 'Type', 'Requests'))
    print('')

    # loop through and print identity name, type and total requests
    for i in r['data']:
        print(row_format.format(i['identity']['label'], i['identity']['type']['type'], i['counts']['requests']))