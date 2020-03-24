from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Template, Context

from NEMO.forms import AlertForm
from NEMO.models import Alert, AlertCategory, User
from NEMO.utilities import bootstrap_primary_color, format_datetime
from NEMO.views.customization import get_customization, get_media_file_contents

@staff_member_required(login_url=None)
@require_http_methods(['GET', 'POST'])
def alerts(request):
	alert_id = request.GET.get('alert_id') or request.POST.get('alert_id')
	try:
		alert = Alert.objects.get(id=alert_id)
	except Alert.DoesNotExist:
		alert = None
	if request.method == 'GET':
		form = AlertForm(instance=alert)
	elif request.method == 'POST':
		form = AlertForm(data=request.POST, instance=alert)
		if form.is_valid():
			alert = form.save()
			if not alert.creator:
				alert.creator = request.user
			alert.save()
			form = AlertForm()
	else:
		form = AlertForm()
	dictionary = {
		'form': form,
		'editing': True if form.instance.id else False,
		'alerts': Alert.objects.filter(user=None, expired=False, deleted=False),
		'alert_categories': AlertCategory.objects.all()
	}
	delete_expired_alerts()
	return render(request, 'alerts.html', dictionary)


@login_required
@require_POST
def delete_alert(request, alert_id):
	try:
		alert = get_object_or_404(Alert, id=alert_id)
		if alert.user == request.user:  # Users can delete their own alerts
			alert.deleted = True
			alert.save(update_fields=['deleted'])
		elif alert.user is None and request.user.is_staff:  # Staff can delete global alerts
			alert.deleted = True
			alert.save(update_fields=['deleted'])
	except Http404:
		pass
	return redirect(request.META.get('HTTP_REFERER', 'landing'))


def delete_expired_alerts():
	Alert.objects.filter(expiration_time__lt=timezone.now()).delete()

def send_alert_emails(alert):
	user_office_email = get_customization('user_office_email_address')
	facility_name = get_customization('facility_name')
	if facility_name == '':
		facility_name = "Facility"
	generic_email = get_media_file_contents('generic_email.html')
	if user_office_email and generic_email:
		users = User.objects.filter(is_active=True).exclude(is_staff=True)
		subject = alert.title
		title = f"{facility_name} Alert"
		color = bootstrap_primary_color('danger')
		greeting = 'Labmembers,'
		message = alert.contents
		dictionary = {
			'title': title,
			'greeting': greeting,
			'contents': message,
			'template_color': color,
		}
		msg = Template(generic_email).render(Context(dictionary))
		users = [x.email for x in users]
		email = EmailMultiAlternatives(subject, from_email=user_office_email, to=[user_office_email], bcc=set(users))
		email.attach_alternative(msg, 'text/html')
		email.send()
