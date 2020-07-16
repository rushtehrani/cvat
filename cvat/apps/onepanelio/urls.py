# Copyright (C) 2020 Onepanel Inc.
#
# SPDX-License-Identifier: MIT

from django.urls import path
from . import views

urlpatterns = [
    path('workflow_templates', views.get_workflow_templates),
]
