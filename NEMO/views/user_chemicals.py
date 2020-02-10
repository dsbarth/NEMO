from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Context, Template
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.utils import timezone

from NEMO.forms import ChemicalRequestForm, ChemicalRequestApprovalForm, UserChemicalForm, UserChemicalUpdateForm
from NEMO.models import ChemicalRequest, User, UserChemical
from NEMO.views.customization import get_media_file_contents, get_customization
from NEMO.utilities import format_datetime

@login_required
@require_http_methods(['GET', 'POST'])
def chemical_request(request):
	dictionary = {}
	if request.method == 'POST':
		form = ChemicalRequestForm(request.user, data=request.POST)
		if form.is_valid():
			issue = form.save()
			send_new_chemical_request_email(issue)
			dictionary = {
				'title': 'Request received',
				'heading': 'Your request has been received and will be evaluated by the staff',
			}
		else:
			dictionary = {
				'title': 'Chemical request failed',
				'heading': 'Invalid form data',
				'content': str(form.errors),
			}
		return render(request, 'acknowledgement.html', dictionary)
	return render(request, 'user_chemicals/chemical_request.html', dictionary)

@staff_member_required(login_url=None)
@require_GET
def view_requests(request, sort_by=''):
	dictionary = {}
	all_requests = ChemicalRequest.objects.all()
	if sort_by in ['requester', 'chemical_name', 'approved']:
		all_requests = all_requests.order_by(sort_by)
	else:
		all_requests = all_requests.order_by('-date')
	dictionary['all_requests'] = all_requests
	pending_requests = all_requests.filter(approved=0)
	dictionary['pending_requests'] = pending_requests
	return render(request, 'user_chemicals/view_requests.html', dictionary)

@staff_member_required(login_url=None)
@require_http_methods(['GET', 'POST'])
def request_details(request, request_id):
	chem_req = get_object_or_404(ChemicalRequest, id=request_id)

	dictionary = {
		'chemical_request': chem_req,
	}

	return render(request, 'user_chemicals/request_details.html', dictionary)

def send_new_chemical_request_email(chemical_request):
	try:
		safety_email = get_customization('safety_email_address')
		user_office_email = get_customization('user_office_email_address')
		sender = user_office_email
		requester = chemical_request.requester.get_full_name()
		recipient_list = [safety_email]
		subject = f'New Material Request from {requester}'
		body = f'{requester} has submitted a request to bring the following material into the cleanroom: {chemical_request.chemical_name}. <br><br>Please review this request and respond through NEMO.'
		email = EmailMultiAlternatives(subject, from_email=sender, to=recipient_list)
		email.attach_alternative(body, 'text/html')
		email.send()
	except:
		pass

@staff_member_required(login_url=None)
@require_http_methods(['GET', 'POST'])
def update_request(request, request_id):
	chemical_request = get_object_or_404(ChemicalRequest, id=request_id)
	form = ChemicalRequestApprovalForm(request.user, data=request.POST, instance=chemical_request)
	if not form.is_valid():
		dictionary = {
			'title': 'Chemical request update failed',
			'heading': 'Invalid form data',
			'content': str(form.errors),
		}
		return render(request, 'acknowledgement.html', dictionary)
	chem_req = form.save()
	send_chemical_request_email_update(chem_req)
	return redirect('view_requests')

def send_chemical_request_email_update(chemical_request):
	try:
		safety_email = get_customization('safety_email_address')
		user_office_email = get_customization('user_office_email_address')
		sender = user_office_email
		recipient_list = [safety_email, chemical_request.requester.email]
		subject = f'Update to your Material Request for {chemical_request.chemical_name}'
		body = f'''{chemical_request.requester.get_short_name()},<br><br>
		{chemical_request.approver.get_full_name()} has responded to your material request for
		{chemical_request.chemical_name} with the following comments:<br><br>
		{chemical_request.approval_comments}<br>
		The current status of your request is {chemical_request.get_approved_display()}.<br>
		Please reply to this email if you have any questions.<br><br>
		Best,<br>
		PRISM Cleanroom Staff'''
		email = EmailMultiAlternatives(subject, from_email=sender, to=recipient_list)
		email.attach_alternative(body, 'text/html')
		email.send()
	except:
		pass

@staff_member_required(login_url=None)
@require_GET
def user_chemicals(request, sort_by=''):
	dictionary = {}
	user_chemicals = UserChemical.objects.all()
	if sort_by in ['owner', 'chemical_name', 'in_date', 'expiration', 'location', 'label_id']:
		user_chemicals = user_chemicals.order_by(sort_by)
	else:
		user_chemicals = user_chemicals.order_by('location')
	dictionary['user_chemicals'] = user_chemicals
	return render(request, 'user_chemicals/user_chemicals.html', dictionary)

@staff_member_required(login_url=None)
@require_http_methods(['GET', 'POST'])
def add_user_chemical(request, chem_req=''):
	dictionary={
		'one_year_from_now': timezone.now() + timedelta(days=365)
	}
	users = User.objects.filter(is_active=True)
	dictionary['users'] = users
	if chem_req:
		chemical_request = get_object_or_404(ChemicalRequest, id=chem_req)
		dictionary['chemical_request'] = chemical_request
	if request.method == 'POST':
		form = UserChemicalForm(data=request.POST)
		if not form.is_valid():
			dictionary = {
				'title': 'Chemical request update failed',
				'heading': 'Invalid form data',
				'content': str(form.errors),
			}
			return render(request, 'acknowledgement.html', dictionary)
		user_chem = form.save()
		chem_req =  request.POST.get('chem_request')
		if chem_req:
			chemical_request = get_object_or_404(ChemicalRequest, id=chem_req)
			user_chem.request = chemical_request
			user_chem.save()
		return HttpResponseRedirect(reverse('user_chemicals'))
	return render(request, 'user_chemicals/add_user_chemical.html', dictionary)


@staff_member_required(login_url=None)
@require_http_methods(['GET', 'POST'])
def update_user_chemical(request, chem_id):
	user_chem = get_object_or_404(UserChemical, id=chem_id)
	if request.method == 'GET':
		form = UserChemicalForm(instance=user_chem)
		owner = user_chem.owner
		dictionary = {
			'form': form,
			'one_year_from_now': timezone.now() + timedelta(days=365),
			'users': User.objects.filter(is_active=True),
			'owner': owner,
		}
		return render(request, 'user_chemicals/update_user_chemical.html', dictionary)
	elif request.method == 'POST':
		user_chem = get_object_or_404(UserChemical, id=chem_id)
		form = UserChemicalForm(data=request.POST, instance=user_chem)
		if not form.is_valid():
			dictionary = {
				'title': 'Chemical request update failed',
				'heading': 'Invalid form data',
				'content': str(form.errors),
			}
			return render(request, 'acknowledgement.html', dictionary)
		user_chem = form.save()
		return HttpResponseRedirect(reverse('user_chemicals'))
	return HttpResponseRedirect(reverse('user_chemicals'))

@staff_member_required(login_url=None)
@require_POST
def delete_user_chemical(request, chem_id):
	try:
		user_chem = UserChemical.objects.get(id=chem_id)
		user_chem.delete()
	except UserChemical.DoesNotExist:
		pass
	return redirect(reverse('user_chemicals'))
