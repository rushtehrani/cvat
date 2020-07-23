# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import os

from django.http import JsonResponse

from cvat.apps.authentication.decorators import login_required
from cvat.apps.onepanelio.models import AuthToken
import time
import onepanel.core.api
from onepanel.core.api.rest import ApiException
from pprint import pprint

def get_workflow_templates(request):
    auth_token = AuthToken.get_auth_token(request)
    configuration = onepanel.core.api.Configuration()
    # Configure API key authorization: Bearer
    configuration.api_key['authorization'] = auth_token
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['authorization'] = 'Bearer'

    # Defining host is optional and default to http://localhost:8888
    configuration.host = os.getenv('ONEPANEL_API_URL')

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



def get_node_pool(request):
    auth_token = AuthToken.get_auth_token(request)
    configuration = onepanel.core.api.Configuration()
    # Configure API key authorization: Bearer
    configuration.api_key['authorization'] = auth_token
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['authorization'] = 'Bearer'

    # Defining host is optional and default to http://localhost:8888
    configuration.host = os.getenv('ONEPANEL_API_URL')

    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.ConfigServiceApi(api_client)
    
    try:
        api_response = api_instance.get_config()
        pprint(api_response)
        return JsonResponse(api_response.to_dict()) #send only node pool?
        
    except ApiException as e:
        print("Exception when calling ConfigServiceApi->get_config: %s\n" % e)


def get_object_counts(request, pk):
    # db_task = self.get_object()
    data = annotation.get_task_data_custom(pk, request.user)
    return Response(data)

def get_model_keys(request, pk):
    # db_task = self.get_object()
    form_data = request.data
    S3 = boto3.client('s3')
    paginator = S3.get_paginator('list_objects_v2')
    keys = set()
    for page in paginator.paginate(Bucket=os.getenv('AWS_BUCKET_NAME'), Prefix=os.getenv('AWS_S3_PREFIX','datesets')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'):
        try:
            contents = page['Contents']
        except KeyError as e:
            wlogger.warning("An exception occurred. {}".format(e))
            break

        for cont in contents:
            # print(cont['Key'])
            key = cont['Key']
            if "models" in key and "saved_model" not in key and "logs" not in key:
                if form_data['model_type'] == "tensorflow":
                    if "tfod" in key:
                        keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
                else:
                    if "maskrcnn" in key:
                        keys.add(os.path.join(*(os.path.dirname(cont['Key']).split(os.path.sep)[2:])))
    return Response({'keys':keys})

def get_workflow_parameters(request):
    """This function should return a list/dict of parameters for selected workflow.
    Additionally, use default values to pre-populate fields.

    """
    pass

def create_annotation_model(request, pk):
    db_task = self.get_object()
    db_labels = db_task.label_set.prefetch_related('attributespec_set').all()
    db_labels = {db_label.id:db_label.name for db_label in db_labels}
    num_classes = len(db_labels.values())

    slogger.glob.info("Createing annotation model for task: {} with num_classes {}".format(db_task.name,num_classes))

    form_data = request.data
    slogger.glob.info("Form data without preprocessing {} {}".format(form_data, type(form_data)))
    # form_data = json.loads(next(iter(form_data.dict().keys())))
    # slogger.glob.info("form data {}".format(form_data))
    # Parse any extra arguments
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
    # print(args_and_vals)
    # print("db",db_task)
    # print(db_task.owner.username,"name")
    # self.export_annotations_for_model(pk,form_data)
    project = dm.TaskProject.from_task(
        Task.objects.get(pk=form_data['project_uid']), db_task.owner.username)


    #check if datasets folder exists on aws bucket
    s3_client = boto3.client('s3')
    # print(os.getenv('AWS_BUCKET_NAME'))
    if os.getenv("AWS_BUCKET_NAME", None) is None:
        msg = "AWS_BUCKET_NAME environment var does not exist. Please add ENV var with bucket name."
        slogger.glob.info("AWS_BUCKET_NAME environment var does not exist. Please add ENV var with bucket name.")
        return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)

    aws_s3_prefix = os.getenv('AWS_S3_PREFIX','datasets')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+os.getenv('ONEPANEL_RESOURCE_UID')+'/datasets/'
    try:
        s3_client.head_object(Bucket=os.getenv('AWS_BUCKET_NAME'), Key=aws_s3_prefix)
        # print("exists")
        #add logging
    except ClientError:
        # Not found
        slogger.glob.info("Datasets folder does not exist in the bucket, creating a new one.")
        s3_client.put_object(Bucket=os.getenv('AWS_BUCKET_NAME'), Key=(aws_s3_prefix))

    # TODO: create dataset and dump locally and push to s3
    # TODO: folder name should have timestamp
    #project_uid is actually a task id
    with tempfile.TemporaryDirectory() as test_dir:
        #print(test_dir)
        

        #print(os.listdir(test_dir))
        if "TFRecord" in form_data['dump_format']:
            dataset_name = db_task.name+"_tfrecords_"+stamp
            dataset_path_aws = os.path.join("datasets",dataset_name)
            project.export("cvat_tfrecord", test_dir, save_images=True)
            s3_client.put_object(Bucket=os.getenv('AWS_BUCKET_NAME'), Key=(aws_s3_prefix+dataset_name+'/'))
            s3_client.upload_file(os.path.join(test_dir, 'default.tfrecord'), os.getenv('AWS_BUCKET_NAME'),aws_s3_prefix+dataset_name+'/default.tfrecord')
            s3_client.upload_file(os.path.join(test_dir, 'label_map.pbtxt'), os.getenv('AWS_BUCKET_NAME'),aws_s3_prefix+dataset_name+'/label_map.pbtxt')
        else:
            dataset_name = db_task.name+"_coco_"+stamp
            dataset_path_aws = os.path.join("datasets",dataset_name)
            project.export("cvat_coco", test_dir, save_images=True)
            s3_client.put_object(Bucket=os.getenv('AWS_BUCKET_NAME'), Key=(aws_s3_prefix+dataset_name+'/annotations/'))
            s3_client.put_object(Bucket=os.getenv('AWS_BUCKET_NAME'), Key=(aws_s3_prefix+dataset_name+'/images/'))
            s3_client.upload_file(os.path.join(test_dir, "annotations/instances_default.json"),os.getenv('AWS_BUCKET_NAME'),aws_s3_prefix+dataset_name+"/annotations/instances_default.json")

            for root,dirs,files in os.walk(os.path.join(test_dir, "images")):
                for file in files:
                    print(os.path.join(root, file))
                    s3_client.upload_file(os.path.join(test_dir,"images",file),os.getenv('AWS_BUCKET_NAME'),os.path.join(aws_s3_prefix+dataset_name+"/images/", file))

    #execute workflow
    configuration = onepanel.core.api.Configuration()
    # # Configure API key authorization: Bearer
    # configuration.api_key['authorization'] = AuthToken.get_auth_token(request)
    # locally use env var
    configuration.api_key['authorization'] = os.getenv('ONEPANEL_AUTHORIZATION')
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['authorization'] = 'Bearer'
    # Defining host is optional and default to http://localhost:8888
    configuration.host = os.getenv('ONEPANEL_API_URL')
    # Enter a context with an instance of the API client
    with onepanel.core.api.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = onepanel.core.api.WorkflowServiceApi(api_client)
        namespace = os.getenv('ONEPANEL_RESOURCE_NAMESPACE') # str | 
        params = []
        # params.append(Parameter(name="source", value="https://github.com/onepanelio/Mask_RNN.git"))
        params.append(Parameter(name="dataset-path", value=aws_s3_prefix+dataset_name))
        params.append(Parameter(name="bucket-name", value=os.getenv('AWS_BUCKET_NAME')))
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
            slogger.glob.info("TF ref model path {}".format(ref_model_path))
            params.append(Parameter(name='model-path',value=os.getenv('AWS_S3_PREFIX','datasets')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+os.getenv('ONEPANEL_RESOURCE_UID')+'/models/'+db_task.name+"_tfod_"+form_data['ref_model']+'_'+stamp+'/'))
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
            slogger.glob.info("maskrcnn ref model path {}".format(ref_model_path))
            params.append(Parameter(name='model-path',value=os.getenv('AWS_S3_PREFIX')+'/'+os.getenv('ONEPANEL_RESOURCE_NAMESPACE')+'/'+os.getenv('ONEPANEL_RESOURCE_UID')+'/models/'+db_task.name+"_maskrcnn_"+stamp+'/'))
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

