# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function
from cvat.apps.authentication.decorators import login_required
from cvat.apps.onepanelio.models import AuthToken
import time
import onepanel.core.api
from onepanel.core.api.rest import ApiException
from pprint import pprint

@login_required
def get_workflow_templates(request):
    auth_token = AuthToken.get_auth_token(request)
    configuration = onepanel.core.api.Configuration()
    # Configure API key authorization: Bearer
    configuration.api_key['authorization'] = auth_token
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['authorization'] = 'Bearer'

    # Defining host is optional and default to http://localhost:8888
    configuration.host = "http://localhost:8888"

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowTemplateServiceApi(api_client)
        namespace = 'namespace_example' # str |
    page_size = 100 # int |  (optional)
    page = 1 # int |  (optional)
    try:
        api_response = api_instance.list_workflow_templates(namespace, page_size=page_size, page=page)
        pprint(api_response)
        return api_response
    except ApiException as e:
        print("Exception when calling WorkflowTemplateServiceApi->list_workflow_templates: %s\n" % e)
