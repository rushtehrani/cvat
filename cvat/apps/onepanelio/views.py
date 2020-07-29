# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import os, json
from tempfile import mkstemp
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
import cvat.apps.dataset_manager.task as dm
from rest_framework import status

import time
from datetime import datetime
import onepanel.core.api
from onepanel.core.api.rest import ApiException
from onepanel.core.api.models import Parameter

from pprint import pprint
from rest_framework.decorators import api_view
import yaml



def onepanel_authorize():
    # auth_token = AuthToken.get_auth_token(request)
    auth_token = os.getenv('ONEPANEL_AUTHORIZATION')
    configuration = onepanel.core.api.Configuration(
        host = os.getenv('ONEPANEL_API_URL'),
        api_key = { 'Bearer': auth_token})
    configuration.api_key_prefix['Bearer'] = 'Bearer'
    return configuration


def authenticate_aws():
    """ Set appropriate env vars before importing boto3

    """
    with open("/etc/onepanel/artifactRepository") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    
    cloud_provider = list(data.keys())[1]


    with open("/etc/onepanel/artifactRepositoryS3AccessKey") as file:
        access_key = yaml.load(file, Loader=yaml.FullLoader)
        
    with open("/etc/onepanel/artifactRepositoryS3SecretKey") as file:
        secret_key = yaml.load(file, Loader=yaml.FullLoader)

    #set env vars
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key

    return data[cloud_provider]['bucket'], cloud_provider

def get_available_dump_formats():
    data = DatumaroTask.get_export_formats()
    formats = {d['name']:d['tag'] for d in data}
    return formats

@api_view(['POST'])
def get_workflow_templates(request):
    configuration = onepanel_authorize()
    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowTemplateServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')  # str |
    page_size = 100 # int |  (optional)
    page = 1 # int |  (optional)
    try:
        api_response = api_instance.list_workflow_templates(namespace, page_size=page_size, page=page)
        pprint(api_response)
        return JsonResponse(api_response.to_dict())
    except ApiException as e:
        print("Exception when calling WorkflowTemplateServiceApi->list_workflow_templates: %s\n" % e)



@api_view(['POST'])
def get_workflow_parameters(request):
    """This function should return a list/dict of parameters for selected workflow.
    Additionally, use default values to pre-populate fields.

    """
    # read workflow_uid and workflow_version from request payload


    configuration = onepanel_authorize()
    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowTemplateServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')  # str |
    try:
        api_response = api_instance.get_workflow_template2(namespace, uid=workflow_uid, version=str(workflow_version))
        pprint(api_response)
        return JsonResponse(api_response.to_dict())
    except ApiException as e:
        print("Exception when calling WorkflowTemplateServiceApi->list_workflow_templates: %s\n" % e)



@api_view(['POST'])
def get_node_pool(request):
    configuration = onepanel_authorize()

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.ConfigServiceApi(api_client)
    
    try:
        api_response = api_instance.get_config()
        pprint(api_response)
        return JsonResponse(api_response.to_dict()['node_pool']['options'])
        
    except ApiException as e:
        print("Exception when calling ConfigServiceApi->get_config: %s\n" % e)

@api_view(['POST'])
def get_object_counts(request, pk):
    # db_task = self.get_object()
    data = annotation.get_task_data_custom(pk, request.user)
    return Response(data)



@api_view(['POST'])
def get_model_keys(request):
    form_data = json.loads(request.body.decode('utf-8'))
    bucket_name = authenticate_aws()
    import boto3
    from botocore.exceptions import ClientError
    S3 = boto3.client('s3')
    paginator = S3.get_paginator('list_objects_v2')
    keys = set()
    for page in paginator.paginate(Bucket=bucket_name, Prefix=os.getenv('AWS_S3_PREFIX','datesets')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'):
        try:
            contents = page['Contents']
        except KeyError as e:
            wlogger.warning("An exception occurred. {}".format(e))
            break

        for cont in contents:
            key = cont['Key']
            if "models" in key and "saved_model" not in key and "logs" not in key:
                if form_data['model_type'] == "tensorflow":
                    if "tfod" in key:
                        keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
                else:
                    if "maskrcnn" in key:
                        keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
    return Response({'keys':keys})



def dump_training_data(uid, db_task, stamp, dump_format, cloud_prefix):

    project = dm.TaskProject.from_task(
        TaskModel.objects.get(pk=uid), db_task.owner.username)

    # read artifactRepository to find out cloud provider and get access for upload
    
    bucket_name, cloud_provider = authenticate_aws()
    
    if dump_format not in list(get_available_dump_formats().keys()):
        dump_format = "cvat_tfrecord"

    with tempfile.TemporaryDirectory() as test_dir:

        project.export(dump_format, test_dir, save_images=True)

        if cloud_provider == "s3":
            
            import boto3
            from botocore.exceptions import ClientError

            #check if datasets folder exists on aws bucket
            s3_client = boto3.client('s3')

            try:
                s3_client.head_object(Bucket=bucket_name, Key=cloud_prefix)
                #add logging
            except ClientError:
                # Not found
                slogger.glob.info("Datasets folder does not exist in the bucket, creating a new one.")
                s3_client.put_object(Bucket=bucket_name, Key=(cloud_prefix))


            dataset_name = os.getenv('ONEPANEL_RESOURCE_UID').replace(' ', '_') + '_' + db_task.name + "_" + dump_format + "_" + stamp
            for root,dirs,files in os.walk(test_dir):
                for file in files:
                    upload_dir = root.replace(test_dir, "")
                    if upload_dir.startswith("/"):
                        upload_dir = upload_dir[1:]
                    s3_client.upload_file(os.path.join(root,file),bucket_name,os.path.join(cloud_prefix,dataset_name, upload_dir, file))
          
        elif cloud_provider == "gcs":
            pass
        
        elif cloud_provider == "az":
            pass

        else:
            raise ValueError("Invalid cloud provider! Should be from ['s3','gcs','az']")

    return bucket_name, dataset_name


@api_view(['POST'])
def create_annotation_model(request, pk):
    """
        Executes workflow selected by User.
    """
    
    db_task = TaskModel.objects.get(pk=pk)
    db_labels = db_task.label_set.prefetch_related('attributespec_set').all()
    db_labels = {db_label.id:db_label.name for db_label in db_labels}
    num_classes = len(db_labels.values())

    slogger.glob.info("Creating annotation model for task: {} with num_classes {}".format(db_task.name,num_classes))

    form_data = json.loads(request.body.decode('utf-8'))
    slogger.glob.info("Form data without preprocessing {} {}".format(form_data, type(form_data)))
 
    form_args = form_data['arguments']
    time = datetime.now()
    stamp = time.strftime("%m%d%Y%H%M%S")

    if "cpu" in form_data['machine_type']:
        tf_image = "tensorflow/tensorflow:1.13.1-py3"
        machine ="Standard_D4s_v3"
    else:
        tf_image = "tensorflow/tensorflow:1.13.1-gpu-py3"
        machine = "Standard_NC6"

    list_of_args = form_args.split(';')
    args_and_vals = {}
    for i in list_of_args:
        if i == "":
            continue
        arg = i.split('=')
        args_and_vals[arg[0]] = arg[1]

    if '--stage1_epochs' not in args_and_vals:
        args_and_vals["--stage1_epochs"] = 1
    if '--stage2_epochs' not in args_and_vals:
        args_and_vals["--stage2_epochs"] = 2
    if '--stage3_epochs' not in args_and_vals:
        args_and_vals["--stage3_epochs"] = 3

    cloud_prefix = os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+ '/annotation-dump/'

    # dump training data on cloud
    bucket_name, dataset_name = dump_training_data(int(form_data['project_uid']), db_task, stamp, form_data['dump_format'], cloud_prefix)
   
    #execute workflow
    configuration = onepanel_authorize()

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE') # str | 
        params = []
        # params.append(Parameter(name="source", value="https://github.com/onepanelio/Mask_RNN.git"))
        params.append(Parameter(name="dataset-path", value=cloud_prefix+dataset_name))
        params.append(Parameter(name="bucket-name", value=bucket_name))
        params.append(Parameter(name='task-name', value=db_task.name))
        # params.append(Parameter(name='num-classes', value=str(num_classes)))
        params.append(Parameter(name='extras', value=json.dumps(args_and_vals).replace(" ","").replace("{","").replace("}","").replace(":","=")))
        params.append(Parameter(name="tf-image", value=tf_image))
        params.append(Parameter(name="sys-node-pool", value=machine))
        if 'TFRecord' in form_data['dump_format']:
            if "base_model" in form_data and "tfod" in form_data['base_model']:
                ref_model_path = os.getenv('AWS_S3_PREFIX')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+form_data['base_model']
            else:
                ref_model_path = ""
            params.append(Parameter(name='model-path',value=os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/workflow_data/models/'+os.getenv('ONEPANEL_RESOURCE_UID')+'_'+db_task.name+"_tfod_"+stamp+'/'))
            params.append(Parameter(name='ref-model-path', value=ref_model_path))
            params.append(Parameter(name='num-classes', value=str(num_classes)))
            params.append(Parameter(name="ref-model", value=form_data['ref_model']))
            body = onepanel.core.api.CreateWorkflowExecutionBody(parameters=params,
            workflow_template_uid = os.getenv('ONEPANEL_OD_TEMPLATE_ID')) 
        else:
            if "base_model" in form_data and "maskrcnn" in form_data['base_model']:
                ref_model_path = os.getenv('AWS_S3_PREFIX')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+form_data['base_model']
            else:
                ref_model_path = ""
            params.append(Parameter(name='model-path',value=os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/workflow_data/models/'+os.getenv('ONEPANEL_RESOURCE_UID')+'_' + db_task.name+"_maskrcnn_"+stamp+'/'))
            params.append(Parameter(name='ref-model-path', value=ref_model_path))
            params.append(Parameter(name='num-classes', value=str(num_classes+1)))
            params.append(Parameter(name='stage-1-epochs', value=str(args_and_vals['--stage1_epochs'])))
            params.append(Parameter(name='stage-2-epochs', value=str(args_and_vals['--stage2_epochs'])))
            params.append(Parameter(name='stage-3-epochs', value=str(args_and_vals['--stage3_epochs'])))
            body = onepanel.core.api.CreateWorkflowExecutionBody(parameters=params,
            workflow_template_uid = os.getenv('ONEPANEL_MASKRCNN_TEMPLATE_ID')) 
        try:
            api_response = api_instance.create_workflow_execution(namespace, body)
            return Response(data="Workflow executed", status=status.HTTP_200_OK)
        except ApiException as e:
            slogger.glob.exception("Exception when calling WorkflowServiceApi->create_workflow_execution: {}\n".format(e))
            return Response(data="error occured", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(data=20, status=status.HTTP_200_OK)

