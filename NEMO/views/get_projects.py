from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET

from NEMO.models import User
from NEMO.views.customization import get_customization


@staff_member_required(login_url=None)
@require_GET
def get_projects(request):
	""" Gets a list of all active projects for a specific user. This is only accessible by staff members. """
	user = get_object_or_404(User, id=request.GET.get('user_id', None))
	projects = user.active_projects()
	source_template = request.GET.get('source_template')
	if source_template == 'training':
		entry_number = int(request.GET['entry_number'])
		return render(request, 'training/get_projects.html', {'projects': projects, 'entry_number': entry_number})
	return JsonResponse(dict(projects=list(projects.values('id', 'name'))))


@staff_member_required(login_url=None)
@require_GET
def get_projects_for_tool_control(request):
	user_id = request.GET.get('user_id')
	user = get_object_or_404(User, id=user_id)
	exclude=get_customization('exclude_from_usage')
	projects_to_exclude = []
	if exclude:
		projects_to_exclude = [int(s) for s in exclude.split() if s.isdigit()]
	return render(request, 'tool_control/get_projects.html', {'active_projects': user.active_projects().exclude(id__in=projects_to_exclude), 'user_id': user_id})


@login_required
@require_GET
def get_projects_for_self(request):
	""" Gets a list of all active projects for the current user. """
	exclude=get_customization('exclude_from_usage')
	projects_to_exclude = []
	if exclude:
		projects_to_exclude = [int(s) for s in exclude.split() if s.isdigit()]
	return render(request, 'tool_control/get_projects.html', {'active_projects': request.user.active_projects().exclude(id__in=projects_to_exclude), 'user_id': request.user.id})
