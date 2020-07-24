# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from django.urls import path
from . import views

urlpatterns = [
    path('workflow_templates', views.get_workflow_templates),
    path('node_pool', views.get_node_pool),
    path('get_object_counts', view.get_object_counts),
    path('get_model_keys', view.get_model_keys),
    path('create_annotation_model', views.create_annotation_model)
]
