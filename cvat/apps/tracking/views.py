
# Copyright (C) 2018-2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
import copy
import json, glob
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from rules.contrib.views import permission_required

from cvat.apps.authentication.decorators import login_required
from cvat.apps.engine.data_manager import TrackManager
from cvat.apps.engine.models import (Job, TrackedShape)
from cvat.apps.engine.serializers import LabeledDataSerializer
from cvat.apps.engine.serializers import (TrackedShapeSerializer)
from cvat.apps.engine.annotation import put_task_data,patch_task_data
from .tracker import RectangleTracker
from cvat.apps.engine.log import slogger



def convert_to_cvat_format(data):
	result = {
		"tracks": [],
		"shapes": [],
		"tags": [],
		"version": 0,
	}

	for label in data:
		boxes = data[label]
		for box in boxes:
			result['shapes'].append({
				"type": "rectangle",
				"label_id": label,
				"frame": box[0],
				"points": [box[1], box[2], box[3], box[4]],
				"z_order": 0,
				"group": None,
				"occluded": False,
				"attributes": [],
			})

	return result


@api_view(['POST'])
@login_required
@permission_required(perm=['engine.task.access'], raise_exception=True)
def tracking(request, tid):
	data = json.loads(request.body.decode('utf-8'))
	# slogger.glob.info("data {}".format(data))
	slogger.glob.info("tracking payload {}".format(data))
	tracking_job = data['trackingJob']
	job_id = data['jobId']
	track = tracking_job['track'] #already in server model
	# Start the tracking with the bounding box in this frame
	start_frame = tracking_job['startFrame']
	# Until track this bounding box until this frame (excluded)
	stop_frame = tracking_job['stopFrame']

	def shape_to_db(tracked_shape_on_wire):
		s = copy.copy(tracked_shape_on_wire)
		s.pop('group', 0)
		s.pop('attributes', 0)
		s.pop('label_id', 0)
		s.pop('byMachine', 0)
		s.pop('keyframe')
		return TrackedShape(**s)

	tracker = RectangleTracker()
	new_shapes, result = tracker.track_rectangles(tid, track['shapes'][0]['points'], start_frame, stop_frame, track['label_id'])

	reset= False
	result = convert_to_cvat_format(result)
	serializer = LabeledDataSerializer(data=result)
	if serializer.is_valid(raise_exception=True):
		if reset:
			put_task_data(tid, request.user, result)
		else:
			patch_task_data(tid, request.user, result, "create")
	return HttpResponse()