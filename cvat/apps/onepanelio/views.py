# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import os, json
import tempfile
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseNotFound
from rest_framework.response import Response

from cvat.apps.authentication.decorators import login_required
from cvat.apps.onepanelio.models import AuthToken
from cvat.apps.engine import annotation
import cvat.apps.dataset_manager.task as DatumaroTask
from cvat.apps.engine.models import Task as TaskModel
from cvat.apps.engine.log import slogger
from rest_framework import status
from datetime import datetime
import onepanel.core.api
from onepanel.core.api.rest import ApiException
from onepanel.core.api.models import Parameter
from rest_framework.decorators import api_view
import yaml

def onepanel_authorize(request):
    #auth_token = AuthToken.get_auth_token(request)
    auth_token = os.getenv('ONEPANEL_AUTHORIZATION')
    configuration = onepanel.core.api.Configuration(
        host = os.getenv('ONEPANEL_API_URL'),
        api_key = { 'Bearer': auth_token})
    configuration.api_key_prefix['Bearer'] = 'Bearer'
    return configuration

def authenticate_cloud_storage():
    """ Set appropriate env vars before importing boto3

    """
    with open("/etc/onepanel/artifactRepository") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    
    cloud_provider = None
    if "s3" in list(data.keys()):  
        cloud_provider = "s3"
    elif "gcs" in list(data.keys()):
        cloud_provider = "gcs"
    elif "az" in list(data.keys()):
        cloud_provider = "az"

    if cloud_provider == "s3":

        with open(os.path.join("/etc/onepanel", data[cloud_provider]['accessKeySecret']['key'])) as file:
            access_key = yaml.load(file, Loader=yaml.FullLoader)
            
        with open(os.path.join("/etc/onepanel", data[cloud_provider]['secretKeySecret']['key'])) as file:
            secret_key = yaml.load(file, Loader=yaml.FullLoader)

        #set env vars
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key

    elif cloud_provider == "gcs":
        #set env vars
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join("/etc/onepanel", data[cloud_provider]['serviceAccountKeySecret']['key'])

    elif cloud_provider == "az":
        pass

    else:
        raise ValueError("Invalid cloud provider. Should be from ['s3', 'gcs', az']")

    return data[cloud_provider]['bucket'], cloud_provider

@api_view(['POST'])
def get_available_dump_formats(request):
    data = DatumaroTask.get_export_formats()
    formats = []
    for d in data:
        formats.append({'name':d['name'], 'tag':d['tag']})
    return JsonResponse({'dump_formats': formats})

@api_view(['POST'])
def get_workflow_templates(request):

    configuration = onepanel_authorize(request)
    
    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowTemplateServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')  # str |
    page_size = 100 # int |  (optional)
    page = 1 # int |  (optional)
    try:
        api_response = api_instance.list_workflow_templates(namespace, page_size=page_size, page=page)
        return JsonResponse(api_response.to_dict())
    except ApiException as e:
        print("Exception when calling WorkflowTemplateServiceApi->list_workflow_templates: %s\n" % e)



@api_view(['POST'])
def get_workflow_parameters(request):
    """This function should return a list/dict of parameters for selected workflow.
    Additionally, use default values to pre-populate fields.

    """
    # read workflow_uid and workflow_version from request payload
    form_data = json.loads(request.body.decode('utf-8'))

    configuration = onepanel_authorize(request)

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowTemplateServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')  # str |
    try:
        api_response = api_instance.get_workflow_template2(namespace, uid=form_data['uid'], version=form_data['version'])
        return JsonResponse({'parameters':api_response.to_dict()['parameters']})
    except ApiException as e:
        print("Exception when calling WorkflowTemplateServiceApi->list_workflow_templates: %s\n" % e)



@api_view(['POST'])
def get_node_pool(request):
    configuration = onepanel_authorize(request)

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.ConfigServiceApi(api_client)
    
    try:
        api_response = api_instance.get_config()
        return JsonResponse({'node_pool':api_response.to_dict()['node_pool']})    
    except ApiException as e:
        print("Exception when calling ConfigServiceApi->get_config: %s\n" % e)

@api_view(['POST'])
def get_object_counts(request, pk):
    # db_task = self.get_object()
    data = annotation.get_task_data_custom(pk, request.user)
    return Response(data)

@api_view(['POST'])
def generate_output_path(request, pk):
    form_data = json.loads(request.body.decode('utf-8'))
    time = datetime.now()
    stamp = time.strftime("%m%d%Y%H%M%S")
    db_task = TaskModel.objects.get(pk=pk)
    dir_name = os.getenv('ONEPANEL_RESOURCE_UID') + '_' + db_task.name + '_' + form_data['uid'] + '_output_' + stamp
    prefix = 'workflow-data/' + os.getenv('ONEPANEL_WORKFLOW_MODEL_DIR','output')
    output = prefix + '/' + dir_name + '/'
    return Response({'name':output})

@api_view(['POST'])
def generate_dataset_path(request, pk):
    form_data = json.loads(request.body.decode('utf-8'))
    time = datetime.now()
    stamp = time.strftime("%m%d%Y%H%M%S")
    db_task = TaskModel.objects.get(pk=pk)
    dir_name = os.getenv('ONEPANEL_RESOURCE_UID') + '_' + db_task.name + '_' + form_data['uid'] + '_annotation_dump_' + stamp
    prefix = 'annotation-dump'
    output = prefix + '/' + dir_name + '/'
    return Response({'name':output})

@api_view(['POST'])
def get_model_keys(request):
    form_data = json.loads(request.body.decode('utf-8'))
    # bucket_name = authenticate_cloud_storage()
    all_models = [x for x in os.listdir("/home/django/share/output") if os.path.isdir("/home/django/share/output/"+x)]
    specific_models = [os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/workflow-data/'+os.getenv('ONEPANEL_WORKFLOW_MODEL_DIR', 'output')+'/'+x for x in all_models if form_data['uid'] in x]
    return Response({'keys':specific_models})

    # import boto3
    # from botocore.exceptions import ClientError
    # S3 = boto3.client('s3')
    # paginator = S3.get_paginator('list_objects_v2')
    # keys = set()
    # for page in paginator.paginate(Bucket=bucket_name, Prefix=os.getenv('AWS_S3_PREFIX','datesets')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'):
    #     try:
    #         contents = page['Contents']
    #     except KeyError as e:
    #         wlogger.warning("An exception occurred. {}".format(e))
    #         break

    #     for cont in contents:
    #         key = cont['Key']
    #         if "models" in key and "saved_model" not in key and "logs" not in key:
    #             if form_data['model_type'] == "tensorflow":
    #                 if "tfod" in key:
    #                     keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
    #             else:
    #                 if "maskrcnn" in key:
    #                     keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
    # return Response({'keys':keys})



def dump_training_data(uid, db_task, stamp, dump_format, cloud_prefix, request):

    project = DatumaroTask.TaskProject.from_task(
        TaskModel.objects.get(pk=uid), db_task.owner.username)

    # read artifactRepository to find out cloud provider and get access for upload
    
    bucket_name, cloud_provider = authenticate_cloud_storage()
    
    data = DatumaroTask.get_export_formats()
    formats = {d['name']:d['tag'] for d in data}
    if dump_format not in formats.values():
        dump_format = "cvat_tfrecord"

    # dataset_name = os.getenv('ONEPANEL_RESOURCE_UID').replace(' ', '_') + '_' + db_task.name + "_" + dump_format + "_" + stamp

    with tempfile.TemporaryDirectory() as test_dir:

        project.export(dump_format, test_dir, save_images=True)

        if cloud_provider == "s3":
            
            import boto3
            from botocore.exceptions import ClientError

            #check if datasets folder exists on aws bucket
            s3_client = boto3.client('s3')
          
            for root,dirs,files in os.walk(test_dir):
                for file in files:
                    upload_dir = root.replace(test_dir, "")
                    if upload_dir.startswith("/"):
                        upload_dir = upload_dir[1:]
                    if not cloud_prefix.endswith("/"):
                        cloud_prefix += "/"
                    s3_client.upload_file(os.path.join(root,file),bucket_name,os.path.join(os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+cloud_prefix, upload_dir, file))
          
        elif cloud_provider == "gcs":
            from google.cloud import storage
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)

            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    upload_dir = root.replace(test_dir, "")
                    if upload_dir.startswith("/"):
                        upload_dir = upload_dir[1:]
                    if not cloud_prefix.endswith("/"):
                        cloud_prefix += "/"
                    blob = bucket.blob(os.path.join(os.getenv('ONEPANEL_RESOURCE_NAMESPACE') + '/'+cloud_prefix, upload_dir, file))
                    blob.upload_from_filename(os.path.join(root, file))
        
        elif cloud_provider == "az":
            pass

        else:
            raise ValueError("Invalid cloud provider! Should be from ['s3','gcs','az']")

    return bucket_name


@api_view(['POST'])
def create_annotation_model(request, pk):
    """
        Executes workflow selected by User.
    """
    
    db_task = TaskModel.objects.get(pk=pk)
    db_labels = db_task.label_set.prefetch_related('attributespec_set').all()
    db_labels = {db_label.id:db_label.name for db_label in db_labels}
    # num_classes = len(db_labels.values())

    form_data = json.loads(request.body.decode('utf-8'))
    slogger.glob.info("Form data without preprocessing {} {}".format(form_data, type(form_data)))
 
    # form_args = form_data['arguments']
    time = datetime.now()
    stamp = time.strftime("%m%d%Y%H%M%S")

    # cloud_prefix = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+ '/annotation-dump/'

    # dump training data on cloud
    if 'sys-annotation-path' in form_data['parameters']:
        bucket_name = dump_training_data(int(pk), db_task, stamp, form_data['dump_format'], form_data['parameters']['sys-annotation-path'], request)
   
    configuration = onepanel_authorize(request)

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE') # str | 
        params = []
        for p_name, p_value in form_data['parameters'].items():
            params.append(Parameter(name=p_name, value=p_value))
        
        body = onepanel.core.api.CreateWorkflowExecutionBody(parameters=params,
        workflow_template_uid = form_data['workflow_template']) 
        try:
            api_response = api_instance.create_workflow_execution(namespace, body)
            return Response(data=api_response.to_dict()['metadata'], status=status.HTTP_200_OK)
        except ApiException as e:
            slogger.glob.exception("Exception when calling WorkflowServiceApi->create_workflow_execution: {}\n".format(e))
            return Response(data="error occured", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(status=status.HTTP_200_OK)

