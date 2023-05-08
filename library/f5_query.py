''' Python Ansible module to return all F5 objects of a certain type in a list '''
import json
from base64 import b64encode
import time

from urllib.parse import urlparse
import requests
from requests.exceptions import RequestException

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'matthewtlincoln@gmail.com'
}

DOCUMENTATION = '''
module: f5_query
short_description: Query F5 LTM/GTM and return all objects of the specified type
description:
    Query F5 LTM and return all objects of the specified type
options:
    f5_url:
        description:
            - url of the F5 device
        required: true
        type: string
    username:
        description:
            - name of user to connect with
        required: true
        type: string
    password:
        description:
            - password of user (no_log)
        required: true
        type: string
    page_size:
        description:
            - number of objects to return per page
        required: false
        type: int
        default: 50
author:
    - Matt Lincoln (mlincoln@paychex.com)
'''

EXAMPLES = '''
f5_query
  f5_url: 'https://{{ f5-url }}//mgmt/tm/ltm/virtual'
  username: {{ username }}
  password: {{ password }}
  page_size: 100
'''


def create_session(user=None, passwd=None, token=None):
    ''' Create requests session with authentication '''

    header = {}
    header['Content-Type'] = 'application/json'
    if None not in [user, passwd]:
        auth_str = b64encode(f"{user}:{passwd}".encode('utf-8')).decode('utf-8')
        header["Authorization"] = f"Basic {auth_str}"
    elif token:
        header['X-F5-Auth-Token'] = token

    new_session = requests.Session()
    new_session.headers.update(header)

    return new_session

def make_request(method, session, allow_404=False, **kwargs):
    ''' Make request calls '''
    method = method.lower()
    avail_methods = ['get', 'post', 'put', 'patch', 'delete']
    return_data = {}
    if method not in avail_methods:
        raise RequestException(f"Invalid method passed:'{method}'. Must be one of {avail_methods}")
    try:
        response = getattr(session, method)(url=kwargs.get('url'),
                                            params=kwargs.get('params', None),
                                            json=kwargs.get('data', None),
                                            verify=False)
        response.raise_for_status()
        try:
            return_data = response.json()
        except ValueError:
            pass
    except requests.exceptions.HTTPError as err:
        if allow_404 and response.status_code == 404:
            return_data = {}
        else:
            try:
                err_content = json.loads(err.response.content)
            except json.JSONDecodeError:
                err_content = err
            err_msg = {"url": kwargs.get('url'),
                       "error": err_content}
            raise RequestException(err_msg).with_traceback(err.__traceback__)

    return response, return_data

def get_auth_token(host, user, passwd):
    ''' Generate authentication token '''

    auth_url = f'https://{host}/mgmt/shared/authn/login'
    auth_body = {'username': f'{user}',
                 'password': f'{passwd}',
                 'loginProviderName': 'tmos'}

    session = create_session(user, passwd)
    status_code, auth_response = make_request(method='POST', session=session, url=auth_url, data=auth_body) # pylint: disable=C0301,W0612
    auth_token = auth_response.get('token', None).get('token', None)

    return auth_token


def query_f5(url, host, auth_token, page_size):
    ''' Query and return a list of virtual server names'''
    next_page = None
    list_url = f'{url}?$select=name&$top={page_size}'
    session = create_session(token=auth_token)
    # Initial query
    status, first_response = make_request(method='GET', session=session, url=list_url) # pylint: disable=W0612
    if 'nextLink' in first_response:
        next_page = first_response['nextLink'].replace("localhost", host)
    page_index = first_response['pageIndex']
    total_pages = first_response['totalPages']
    temp_list = first_response['items']

    # Loop through remaining pages
    while page_index <= total_pages and next_page is not None:
        status, list_response = make_request(method='GET', session=session, url=next_page)
        page_index = list_response['pageIndex']
        temp_list = temp_list + list_response['items']

        if 'nextLink' in list_response:
            next_page = list_response['nextLink'].replace("localhost", host)
        else:
            break

    final_list = []
    for entry in temp_list:
        final_list.append(entry['name'])

    return final_list, len(final_list)

def main():
    ''' The work starts here '''
    fields = {
        "f5_url": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "page_size": {"required": False, "type": "int", "default": 50}
    }

    module = AnsibleModule(argument_spec=fields)
    f5_url = module.params['f5_url']
    f5_host = urlparse(f5_url).hostname
    username = module.params['username']
    password = module.params['password']
    page_size = module.params['page_size']

    results = {"changed": False,
               "list": [],
               "count": "",
               "elapsed_time": ""
              }


    #Do the work
    try:
        auth_token = get_auth_token(f5_host, username, password)
        start_time = time.time()
        results['list'], results['count'] = query_f5(f5_url,f5_host, auth_token, page_size)
        results['elapsed_time'] = f'{time.time() - start_time}'
    except Exception as err: # pylint: disable=W0703
        module.fail_json(msg=str(err))

    module.exit_json(**results)

if __name__ == "__main__":
    main()
