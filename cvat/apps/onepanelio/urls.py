# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from django.urls import path
from . import views

urlpatterns = [
    path('get_workflow_templates', views.get_workflow_templates),
    path('get_node_pool', views.get_node_pool),
    path('get_object_counts/<int:pk>', views.get_object_counts),
    path('get_base_model', views.get_model_keys),
    path('execute_workflow/<int:pk>', views.create_annotation_model)
    path('get_workflow_parameters', view.get_workflow_parameters)
]
