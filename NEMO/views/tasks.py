from smtplib import SMTPException
from textwrap import dedent

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Template, Context
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from NEMO.forms import TaskForm, nice_errors
from NEMO.models import Task, UsageEvent, Interlock, TaskCategory, Reservation, SafetyIssue, TaskStatus, TaskHistory, User
from NEMO.utilities import bootstrap_primary_color, format_datetime
from NEMO.views.customization import get_customization, get_media_file_contents
from NEMO.views.safety import send_safety_email_notification
from NEMO.views.tool_control import determine_tool_status


@login_required
@require_POST
def create(request):
	"""
	This function handles feedback from users. This could be a problem report or shutdown notification.
	"""
	form = TaskForm(request.user, data=request.POST)
	if not form.is_valid():
		dictionary = {
			'title': 'Task creation failed',
			'heading': 'Something went wrong while reporting the problem',
			'content': nice_errors(form).as_ul(),
		}
		return render(request, 'acknowledgement.html', dictionary)
	task = form.save()

	if not settings.ALLOW_CONDITIONAL_URLS and task.force_shutdown:
		dictionary = {
			'title': 'Task creation failed',
			'heading': 'Something went wrong while reporting the problem',
			'content': "Tool control is only available on campus. When creating a task, you can't force a tool shutdown while using NEMO off campus.",
		}
		return render(request, 'acknowledgement.html', dictionary)

	if task.force_shutdown:
		# Shut down the tool.
		task.tool.operational = False
		task.tool.save()
		# End any usage events in progress for the tool.
		UsageEvent.objects.filter(tool=task.tool, end=None).update(end=timezone.now())
		# Lock the interlock for this tool.
		try:
			tool_interlock = Interlock.objects.get(tool__id=task.tool.id)
			tool_interlock.lock()
		except Interlock.DoesNotExist:
			pass

	if task.safety_hazard:
		concern = 'This safety issue was automatically created because a ' + str(task.tool).lower() + ' problem was identified as a safety hazard.\n\n'
		concern += task.problem_description
		issue = SafetyIssue.objects.create(reporter=request.user, location=task.tool.location, concern=concern)
		send_safety_email_notification(request, issue)

	send_new_task_emails(request, task)
	set_task_status(request, task, request.POST.get('status'), request.user)
	return redirect('tool_control')


def send_new_task_emails(request, task):
	message = get_media_file_contents('new_task_email.html')
	if message:
		dictionary = {
			'template_color': bootstrap_primary_color('danger') if task.force_shutdown else bootstrap_primary_color('warning'),
			'user': request.user,
			'task': task,
			'tool': task.tool,
			'tool_control_absolute_url': request.build_absolute_uri(task.tool.get_absolute_url())
		}
		# Send an email to the appropriate NanoFab staff that a new task has been created:
		subject = ('SAFETY HAZARD: ' if task.safety_hazard else '') + task.tool.name + (' shutdown' if task.force_shutdown else ' problem')
		message = Template(message).render(Context(dictionary))
		recipients = tuple([r for r in [task.tool.primary_owner.email, *task.tool.backup_owners.all().values_list('email', flat=True), task.tool.notification_email_address] if r])
		send_mail(subject, '', request.user.email, recipients, html_message=message)

	# Send an email to all users (excluding staff) qualified on the tool:
	user_office_email = get_customization('user_office_email_address')
	message = get_media_file_contents('new_task_email.html')
	if user_office_email and message:
		users = User.objects.filter(qualifications__id=task.tool.id, is_staff=False, is_active=True)
		dictionary = {
			'template_color': bootstrap_primary_color('danger') if task.force_shutdown else bootstrap_primary_color('warning'),
			'user': request.user,
			'task': task,
			'tool': task.tool,
			'tool_control_absolute_url': request.build_absolute_uri(task.tool.get_absolute_url()),
			'labmember': True
		}
		subject = task.tool.name + (' shutdown' if task.force_shutdown else ' problem')
		users = [x.email for x in users]
		rendered_message = Template(message).render(Context(dictionary))
		#try:
		email = EmailMultiAlternatives(subject, from_email=user_office_email, bcc=set(users))
		email.attach_alternative(rendered_message, 'text/html')
		email.send()
		#except SMTPException as e:
		#	dictionary = {
		#		'title': 'Email not sent',
		#		'heading': 'There was a problem sending your email',
		#		'content': 'NEMO was unable to send the email through the email server. The error message that NEMO received is: ' + str(e),
		#	}

def send_task_update_emails(request, task):
	message = get_media_file_contents('generic_email.html')
	user_office_email = get_customization('user_office_email_address')
	if message and user_office_email:
		task.refresh_from_db()
		if not task.tool.problematic():
			tool_status = 'up'
		elif task.tool.operational:
			tool_status = 'in problem status'
		else:
			tool_status = 'down'
		if task.resolved:
			subject = f'{task.tool} Issue Resolved'
			task_user = task.resolver
		elif task.cancelled:
			subject = f'{task.tool} Issue Cancelled'
			task_user = task.resolver
		else:
			subject = f'{task.tool} Update'
			task_user = task.last_updated_by
		messagebody = f"""
	The status of the {task.tool} was just modified by {task_user}.
	You can see the full status description here: {request.build_absolute_uri(task.tool.get_absolute_url())}.

	{task.tool} is currently {tool_status}.
	"""
	if task.resolved:
		messagebody += f"""
	Resolution description:
	{task.resolution_description}
	"""
	dictionary = {
		'template_color': bootstrap_primary_color('success') if tool_status == 'up' else bootstrap_primary_color('warning'),
		'title': subject,
		'greeting': f'{task.tool} Users,',
		'contents': messagebody
	}
	users = User.objects.filter(qualifications__id=task.tool.id, is_active=True)
	users = [x.email for x in users]
	rendered_message = Template(message).render(Context(dictionary))
	try:
		email = EmailMultiAlternatives(subject, from_email=user_office_email, bcc=set(users))
		email.attach_alternative(rendered_message, 'text/html')
		email.send()
	except SMTPException as e:
		dictionary = {
			'title': 'Email not sent',
			'heading': 'There was a problem sending your email',
			'content': 'NEMO was unable to send the email through the email server. The error message that NEMO received is: ' + str(e),
		}


@login_required
@require_POST
def cancel(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	if task.cancelled or task.resolved:
		dictionary = {
			'title': 'Task cancellation failed',
			'heading': 'You cannot cancel this task',
			'content': 'The status of this task has been changed so you may no longer cancel it.',
		}
		return render(request, 'acknowledgement.html', dictionary)
	if task.creator.id != request.user.id:
		dictionary = {
			'title': 'Task cancellation failed',
			'heading': 'You cannot cancel this task',
			'content': 'You may only cancel a tasks that you created.',
		}
		return render(request, 'acknowledgement.html', dictionary)
	task.cancelled = True
	task.resolver = request.user
	task.resolution_time = timezone.now()
	task.save()
	determine_tool_status(task.tool)
	send_task_update_emails(request, task)
	return redirect('tool_control')


def micromanage(task, url):
	# If there's no micromanager present, let the techs do their job and leave them alone...
	if not hasattr(settings, 'MICROMANAGER'):
		return

	# Otherwise, let the micromanagement begin...
	task.refresh_from_db()
	if task.resolved:
		subject = f'{task.tool} task resolved'
	else:
		subject = f'{task.tool} task updated'
	message = f"""
A task for the {task.tool} was just modified by {task.last_updated_by}.

The latest update is at the bottom of the description. The entirety of the task status follows:

Task problem description:
{task.problem_description}

Task progress description:
{task.progress_description}

Task resolution description:
{task.resolution_description}

Visit {url} to view the tool control page for the task.
"""
	send_mail(subject, message, settings.SERVER_EMAIL, settings.MICROMANAGER)


@staff_member_required(login_url=None)
@require_POST
def update(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	form = TaskForm(request.user, data=request.POST, instance=task)
	next_page = request.POST.get('next_page', 'tool_control')
	if not form.is_valid():
		dictionary = {
			'title': 'Task update failed',
			'heading': 'Invalid task form data',
			'content': str(form.errors),
		}
		return render(request, 'acknowledgement.html', dictionary)
	form.save()
	set_task_status(request, task, request.POST.get('status'), request.user)
	determine_tool_status(task.tool)
	send_task_update_emails(request, task)
	try:
		micromanage(task, request.build_absolute_uri(task.tool.get_absolute_url()))
	except:
		pass
	if next_page == 'maintenance':
		return redirect('maintenance')
	else:
		return redirect('tool_control')


@staff_member_required(login_url=None)
@require_GET
def task_update_form(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	categories = TaskCategory.objects.filter(stage=TaskCategory.Stage.INITIAL_ASSESSMENT)
	dictionary = {
		'categories': categories,
		'urgency': Task.Urgency.Choices,
		'task': task,
		'task_statuses': TaskStatus.objects.exclude(name="default"),
	}
	return render(request, 'tasks/update.html', dictionary)


@staff_member_required(login_url=None)
@require_GET
def task_resolution_form(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	categories = TaskCategory.objects.filter(stage=TaskCategory.Stage.COMPLETION)
	dictionary = {
		'categories': categories,
		'task': task,
	}
	return render(request, 'tasks/resolve.html', dictionary)


def set_task_status(request, task, status_name, user):

	if not user.is_staff and status_name:
		raise ValueError("Only staff can set task status")

		#If no status is given, assign to default status. This will make sure all tasks have a proper Task History
	if not status_name:
		status_name = "default"

	status = TaskStatus.objects.get_or_create(name=status_name)
	TaskHistory.objects.create(task=task, status=status_name, user=user, shutdown=task.force_shutdown)

	status_message = f'On {format_datetime(timezone.now())}, {user.get_full_name()} set the status of this task to "{status_name}".'
	task.progress_description = status_message if task.progress_description is None else task.progress_description + '\n\n' + status_message
	task.save()

	message = get_media_file_contents('task_status_notification.html')
	if not message:
		return

	dictionary = {
		'template_color': bootstrap_primary_color('success'),
		'title': f'{task.tool} task notification',
		'status_message': status_message,
		'notification_message': status.notification_message,
		'task': task,
		'tool_control_absolute_url': request.build_absolute_uri(task.tool.get_absolute_url())
	}
	# Send an email to the appropriate NanoFab staff that a new task has been created:
	subject = f'{task.tool} task notification'
	message = Template(message).render(Context(dictionary))
	recipients = [
		task.tool.primary_tool_owner.email if status.notify_primary_tool_owner else None,
		task.tool.notification_email_address if status.notify_tool_notification_email else None,
		status.custom_notification_email_address
	]
	if status.notify_backup_tool_owners:
		recipients += task.tool.backup_tool_owners.values_list('email')
	recipients = filter(None, recipients)
	send_mail(subject, '', user.email, recipients, html_message=message)
