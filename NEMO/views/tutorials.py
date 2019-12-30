from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import Template, RequestContext, Context
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from NEMO.models import User, Project
from NEMO.utilities import send_mail
from NEMO.views.customization import get_customization, get_media_file_contents


@login_required
@require_http_methods(['GET', 'POST'])
def nanofab_rules(request):
	if request.method == 'GET' and (request.user.training_required or request.user.is_staff):
		tutorial = get_media_file_contents('nanofab_rules_tutorial.html')
		if tutorial:
			dictionary = {
				'active_user_count': User.objects.filter(is_active=True).count(),
				'active_project_count': Project.objects.filter(active=True).count(),
			}
			tutorial = Template(tutorial).render(RequestContext(request, dictionary))
		return render(request, 'nanofab_rules.html', {'nanofab_rules_tutorial': tutorial})
	elif request.method == 'POST':
		summary = request.POST.get('making_reservations_summary', '').strip()[:3000]
		dictionary = {
			'user': request.user,
			'making_reservations_rule_summary': summary,
		}
		abuse_email = get_customization('abuse_email_address')
		email_contents = get_media_file_contents('nanofab_rules_tutorial_email.html')
		if abuse_email and email_contents:
			message = Template(email_contents, dictionary).render(Context(dictionary))
			send_mail('PRISM Cleanroom rules tutorial', message, abuse_email, [abuse_email])
		dictionary = {
			'title': 'PRISM Cleanroom rules tutorial',
			'heading': 'Tutorial complete!',
			'content': 'Tool usage and reservation privileges have been enabled on your user account.',
		}
		request.user.training_required = False
		try:
			request.user.access_expiration = request.user.access_expiration.replace(year=request.user.access_expiration.year+1)
		except ValueError:
			request.user.access_expiration = request.user.access_expiration.replace(year=request.user.access_expiration.year+1, day = request.user.access_expiration.day-1)
		request.user.save()
		return render(request, 'acknowledgement.html', dictionary)
	else:
		dictionary = {
			'title': 'Rules tutorial unavailable',
			'heading': 'The rules tutorial is not available to you at this time.',
			'content': 'If you think this is an error, please contact staff.',
		}
		return render(request, 'acknowledgement.html', dictionary)
