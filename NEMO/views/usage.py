from logging import getLogger
from json import loads
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.http import HttpResponse
from requests import get

from xlsxwriter.workbook import Workbook

from NEMO.models import AreaAccessRecord, Reservation, StaffCharge, TrainingSession, UsageEvent, User, Project, Account, StockroomWithdraw, Tool
from NEMO.utilities import get_month_timeframe, month_list, parse_start_and_end_date


logger = getLogger(__name__)


# Class for Applications that can be used for autocomplete
class Application(object):
	def __init__(self, name):
		self.name = name
		self.id = name

	def __str__(self):
		return self.name


# We want to keep all the parameters of the request when switching tabs, so we are just replacing usage <-> billing urls
def get_url_for_other_tab(request):
	full_path_request = request.get_full_path()
	usage_url = reverse('usage')
	billing_url = reverse('usage_billing')
	project_usage_url = reverse('project_usage')
	project_billing_url = reverse('project_billing')
	if project_usage_url in full_path_request:
		full_path_request = full_path_request.replace(project_usage_url, project_billing_url)
	elif project_billing_url in full_path_request:
		full_path_request = full_path_request.replace(project_billing_url, project_usage_url)
	elif usage_url in full_path_request:
		full_path_request = full_path_request.replace(usage_url, billing_url)
	elif billing_url in full_path_request:
		full_path_request = full_path_request.replace(billing_url, usage_url)
	return full_path_request


def get_project_applications():
	applications = []
	projects = Project.objects.filter(id__in=Project.objects.values('application_identifier').distinct().values_list('id', flat=True))
	for project in projects:
		if not any(list(filter(lambda app: app.name == project.application_identifier, applications))):
			applications.append(Application(project.application_identifier))
	return applications


def date_parameters_dictionary(request):
	if request.GET.get('start_date') and request.GET.get('end_date'):
		start_date, end_date = parse_start_and_end_date(request.GET.get('start_date'), request.GET.get('end_date'))
	else:
		start_date, end_date = get_month_timeframe()
	kind = request.GET.get("type")
	identifier = request.GET.get("id")
	customer = request.GET.get("customer")
	tool = request.GET.get("tool")
	dictionary = {
		'month_list': month_list(),
		'start_date': start_date,
		'end_date': end_date,
		'kind': kind,
		'identifier': identifier,
		'tab_url': get_url_for_other_tab(request),
		'customer': None,
		'tool': None,
	}
	if request.user.is_staff:
		dictionary['users'] = User.objects.all()
		dictionary['tools'] = Tool.objects.all()
	try:
		if customer:
			dictionary['customer'] = User.objects.get(id=customer)
		if tool:
			dictionary['tool'] = Tool.objects.get(id=tool)
	except:
		pass
	return dictionary, start_date, end_date, kind, identifier


@login_required
@require_GET
def usage(request):
	base_dictionary, start_date, end_date, kind, identifier = date_parameters_dictionary(request)
	dictionary = get_usage(start_date, end_date, user=request.user)
	dictionary['no_charges'] = not (dictionary['area_access'] or dictionary['stockroom_purchases'] or dictionary['missed_reservations'] or dictionary['staff_charges'] or dictionary['training_sessions'] or dictionary['usage_events'])
	return render(request, 'usage/usage.html', {**base_dictionary, **dictionary})


@login_required
@require_GET
def usagexlsx(request):
	base_dictionary, start_date, end_date, kind, identifier = date_parameters_dictionary(request)
	if not request.user.is_staff:
		user = request.user
	elif base_dictionary['customer'] and request.user.is_staff:
		user = base_dictionary['customer']
	else:
		user = None
	tool = None
	projects = []
	if request.user.is_staff:
		selection = ''
		try:
			if kind == 'application':
				projects = Project.objects.filter(application_identifier=identifier)
				selection = identifier
			elif kind == 'project':
				projects = [Project.objects.get(id=identifier)]
				selection = projects[0].name
			elif kind == 'account':
				account = Account.objects.get(id=identifier)
				projects = Project.objects.filter(account=account)
				selection = account.name
		except:
			pass
		tool = base_dictionary['tool']

	dictionary = get_usage(start_date,end_date,user,projects,tool)
	area_access = dictionary['area_access'].values('customer__username', 'area__name', 'start', 'end', 'project__name') if dictionary['area_access'] else None
	usage_record = dictionary['usage_events'].values('user__username', 'tool__name', 'start', 'end', 'project__name', 'run_data') if dictionary['usage_events'] else None
	stockroom_purchases = dictionary['stockroom_purchases'].values('customer__username', 'stock__name', 'stock__cost', 'quantity', 'date', 'project__name') if dictionary['stockroom_purchases'] else None
	staff_charges = dictionary['staff_charges'].values('staff_member__username', 'customer__username','start', 'end','project__name') if dictionary['staff_charges'] else None
	date_format_str = 'yyyy/mm/dd hh:mm'
	fn = "usage_report" + "_" + start_date.strftime("%Y%m%d") + "_" + end_date.strftime("%Y%m%d") + ".xlsx"
	response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename = "%s"' % fn
	book = Workbook(response, {'in_memory': True, 'remove_timezone': True})
	date_format = book.add_format({'num_format': date_format_str, 'align': 'left'})
	bold = book.add_format({'bold': True})
	if area_access:
		area_sheet = book.add_worksheet('Area Access')
		area_sheet.set_column(0, 1, 18)
		area_sheet.set_column(2,3,18)
		area_sheet.set_column(5, 5, 50)
		headings = ['Username','Area','Start','End','Duration (Hours)','Project']
		area_sheet.write_row(0,0,headings, bold)
		for row_num, row_data in enumerate(area_access):
			duration = (row_data['end'] - row_data['start']).total_seconds()/60/60
			area_sheet.write(row_num + 1, 0, row_data['customer__username'])
			area_sheet.write(row_num + 1, 1, row_data['area__name'])
			area_sheet.write_datetime(row_num + 1, 2, (row_data['start']).astimezone(tz=None), date_format)
			area_sheet.write_datetime(row_num + 1, 3, (row_data['end']).astimezone(tz=None), date_format)
			area_sheet.write(row_num + 1, 4, duration)
			area_sheet.write(row_num + 1, 5, row_data['project__name'])

	if usage_record:
		usage_sheet = book.add_worksheet('Tool Usage')
		usage_sheet.set_column(0, 0, 12)
		usage_sheet.set_column(1,1,30)
		usage_sheet.set_column(2, 3, 18)
		usage_sheet.set_column(5, 5, 50)
		usage_sheet.set_column(6, 6, 18)
		headings = ['Username','Tool','Start','End','Duration (Hours)','Project']
		if request.user.is_staff:
			headings.append('Run Data')
		usage_sheet.write_row(0,0,headings, bold)
		for row_num, row_data in enumerate(usage_record):
			duration = (row_data['end'] - row_data['start']).total_seconds()/60/60
			usage_sheet.write(row_num + 1, 0, row_data['user__username'])
			usage_sheet.write(row_num + 1, 1, row_data['tool__name'])
			usage_sheet.write_datetime(row_num + 1, 2, (row_data['start']).astimezone(tz=None), date_format)
			usage_sheet.write_datetime(row_num + 1, 3, (row_data['end']).astimezone(tz=None), date_format)
			usage_sheet.write(row_num + 1, 4, duration)
			usage_sheet.write(row_num + 1, 5, row_data['project__name'])
			if row_data['run_data'] and request.user.is_staff:
				count = 1
				for key, value in loads(row_data['run_data']).items():
					try:
						value = float(value)
					except:
						pass
					usage_sheet.write(row_num + 1, 5 + count, key)
					usage_sheet.write(row_num + 1, 5 + count + 1, value)
					count += 2

	if stockroom_purchases:
		stockroom_sheet = book.add_worksheet('Stockroom Purchases')
		stockroom_sheet.set_column(0, 0, 12)
		stockroom_sheet.set_column(1,1,30)
		stockroom_sheet.set_column(4, 4, 18)
		stockroom_sheet.set_column(5, 5, 50)
		headings = ['Username','Item','Quantity','Unit Price','Date','Project']
		stockroom_sheet.write_row(0,0,headings, bold)
		for row_num, row_data in enumerate(stockroom_purchases):
			stockroom_sheet.write(row_num + 1, 0, row_data['customer__username'])
			stockroom_sheet.write(row_num + 1, 1, row_data['stock__name'])
			stockroom_sheet.write(row_num + 1, 2, row_data['quantity'])
			stockroom_sheet.write(row_num + 1, 3, row_data['stock__cost'])
			stockroom_sheet.write_datetime(row_num + 1, 4, (row_data['date']).astimezone(tz=None), date_format)
			stockroom_sheet.write(row_num + 1, 5, row_data['project__name'])

	if staff_charges:
		staffcharge_sheet = book.add_worksheet('Staff Charges')
		staffcharge_sheet.set_column(0, 0, 12)
		staffcharge_sheet.set_column(1,1,14)
		staffcharge_sheet.set_column(2, 3, 18)
		staffcharge_sheet.set_column(5, 5, 50)
		headings = ['Username','Staff Member','Start','End','Duration (Hours)','Project']
		staffcharge_sheet.write_row(0,0,headings, bold)
		for row_num, row_data in enumerate(staff_charges):
			duration = (row_data['end'] - row_data['start']).total_seconds()/60/60
			staffcharge_sheet.write(row_num + 1, 0, row_data['customer__username'])
			staffcharge_sheet.write(row_num + 1, 1, row_data['staff_member__username'])
			staffcharge_sheet.write_datetime(row_num + 1, 2, (row_data['start']).astimezone(tz=None), date_format)
			staffcharge_sheet.write_datetime(row_num + 1, 3, (row_data['end']).astimezone(tz=None), date_format)
			staffcharge_sheet.write(row_num + 1, 4, duration)
			staffcharge_sheet.write(row_num + 1, 5, row_data['project__name'])

	if request.user.is_staff:
		filter_parameters = book.add_worksheet('Filter Parameters')
		filter_parameters.write(0, 0, 'Filter Parameters', bold)
		filter_parameters.write_row(1, 0, ['Start','End','User','Tool','Projects'], bold)
		filter_parameters.write(2, 0, start_date, date_format)
		filter_parameters.write(2, 1, end_date, date_format)
		if user:
			filter_parameters.write(2, 2, user.username)
		if tool:
			filter_parameters.write(2, 3, tool.name)
		if projects:
			for count, proj in enumerate(projects):
				filter_parameters.write(2+count,4,proj.name)
	book.close()

	return response


@login_required
@require_GET
def billing(request):
	base_dictionary, start_date, end_date, kind, identifier = date_parameters_dictionary(request)
	formatted_applications = ','.join(map(str, set(request.user.active_projects().values_list('application_identifier', flat=True))))
	try:
		billing_dictionary = billing_dict(start_date, end_date, request.user, formatted_applications)
		return render(request, 'usage/billing.html', {**base_dictionary, **billing_dictionary})
	except Exception as e:
		logger.warning(str(e))
		return render(request, 'usage/billing.html', base_dictionary)


def get_usage(start_date, end_date, user=None, projects=None, tool=None):

	area_access = None
	usage_events = None
	missed_reservations = None
	staff_charges = None
	stockroom_purchases = None
	training_sessions = None

	try:
		if tool:
			usage_events = UsageEvent.objects.filter(tool=tool.id, end__gt=start_date, end__lte=end_date)
			missed_reservations = Reservation.objects.filter(tool=tool.id, missed=True, end__gt=start_date, end__lte=end_date)
			training_sessions = TrainingSession.objects.filter(tool=tool.id, date__gt=start_date, date__lte=end_date)
			if projects:
				usage_events = usage_events.filter(project__in=projects)
				missed_reservations = missed_reservations.filter(project__in=projects)
				training_sessions = training_sessions.filter(project__in=projects)
			if user:
				usage_events = usage_events.filter(user=user.id)
				missed_reservations = missed_reservations.filter(user=user.id)
				training_sessions = training_sessions.filter(trainee=user.id)
		elif projects:
			area_access = AreaAccessRecord.objects.filter(project__in=projects, end__gt=start_date, end__lte=end_date)
			usage_events = UsageEvent.objects.filter(project__in=projects, end__gt=start_date, end__lte=end_date)
			missed_reservations = Reservation.objects.filter(project__in=projects, missed=True, end__gt=start_date, end__lte=end_date)
			staff_charges = StaffCharge.objects.filter(project__in=projects, end__gt=start_date, end__lte=end_date)
			stockroom_purchases = StockroomWithdraw.objects.filter(project__in=projects, date__gt=start_date, date__lte=end_date)
			training_sessions = TrainingSession.objects.filter(project__in=projects, date__gt=start_date, date__lte=end_date)
			if user:
				area_access = area_access.filter(customer=user.id)
				usage_events = usage_events.filter(user=user.id)
				missed_reservations = missed_reservations.filter(user=user.id)
				staff_charges = staff_charges.filter(customer=user.id)
				stockroom_purchases = stockroom_purchases.filter(customer=user.id)
				training_sessions = training_sessions.filter(trainee=user.id)
		elif user:
			area_access = AreaAccessRecord.objects.filter(customer=user.id, end__gt=start_date, end__lte=end_date)
			usage_events = UsageEvent.objects.filter(user=user.id, end__gt=start_date, end__lte=end_date)
			missed_reservations = Reservation.objects.filter(user=user.id, missed=True, end__gt=start_date, end__lte=end_date)
			staff_charges = StaffCharge.objects.filter(customer=user.id, end__gt=start_date, end__lte=end_date)
			stockroom_purchases = StockroomWithdraw.objects.filter(customer=user.id, date__gt=start_date, date__lte=end_date)
			training_sessions = TrainingSession.objects.filter(trainee=user.id, date__gt=start_date, date__lte=end_date)
	except:
		pass

	dictionary = {
		'accounts_and_applications': set(Account.objects.all()) | set(Project.objects.all()) | set(get_project_applications()),
		'area_access': area_access,
		'missed_reservations': missed_reservations,
		'staff_charges': staff_charges,
		'training_sessions': training_sessions,
		'usage_events': usage_events,
		'stockroom_purchases': stockroom_purchases,
	}

	return dictionary


@staff_member_required(login_url=None)
@require_GET
def project_usage(request):
	base_dictionary, start_date, end_date, kind, identifier = date_parameters_dictionary(request)

	projects = []
	selection = ''
	try:
		if kind == 'application':
			projects = Project.objects.filter(application_identifier=identifier)
			selection = identifier
		elif kind == 'project':
			projects = [Project.objects.get(id=identifier)]
			selection = projects[0].name
		elif kind == 'account':
			account = Account.objects.get(id=identifier)
			projects = Project.objects.filter(account=account)
			selection = account.name
	except:
		pass

	tool = base_dictionary['tool']
	user = base_dictionary['customer']

	dictionary = get_usage(start_date,end_date,user=user,projects=projects,tool=tool)
	dictionary['project_autocomplete'] = True
	dictionary['selection'] = selection
	dictionary['no_charges'] = not (dictionary['area_access'] or dictionary['stockroom_purchases'] or dictionary['missed_reservations'] or dictionary['staff_charges'] or dictionary['training_sessions'] or dictionary['usage_events'])
	return render(request, 'usage/usage.html', {**base_dictionary, **dictionary})


@staff_member_required(login_url=None)
@require_GET
def project_billing(request):
	base_dictionary, start_date, end_date, kind, identifier = date_parameters_dictionary(request)
	base_dictionary['project_autocomplete'] = True
	base_dictionary['accounts_and_applications'] = set(Account.objects.all()) | set(Project.objects.all()) | set(get_project_applications())

	project_id = None
	account_id = None
	formatted_applications = None
	selection = ''
	try:
		if kind == 'application':
			formatted_applications = identifier
			selection = identifier
		elif kind == 'project':
			projects = [Project.objects.get(id=identifier)]
			formatted_applications = projects[0].application_identifier
			project_id = identifier
			selection = projects[0].name
		elif kind == 'account':
			account = Account.objects.get(id=identifier)
			projects = Project.objects.filter(account=account, active=True, account__active=True)
			formatted_applications = ','.join(
				map(str, set(projects.values_list('application_identifier', flat=True)))) if projects else None
			account_id = account.id
			selection = account.name

		base_dictionary['selection'] = selection
		billing_dictionary = billing_dict(start_date, end_date, None, formatted_applications, project_id, account_id=account_id, force_pi=True)
		return render(request, 'usage/billing.html', {**base_dictionary, **billing_dictionary})
	except Exception as e:
		logger.warning(str(e))
		return render(request, 'usage/billing.html', base_dictionary)


def is_user_pi(user, application_pi_row):
	return application_pi_row is not None and (user.username == application_pi_row['username'] or (user.first_name == application_pi_row['first_name'] and user.last_name == application_pi_row['last_name']))


def billing_dict(start_date, end_date, user, formatted_applications, project_id=None, account_id=None, force_pi=None):
	dictionary = {}

	if not settings.BILLING_SERVICE or not settings.BILLING_SERVICE['available']:
		return dictionary

	cost_activity_url = settings.BILLING_SERVICE['cost_activity_url']
	project_lead_url = settings.BILLING_SERVICE['project_lead_url']
	keyword_arguments = settings.BILLING_SERVICE['keyword_arguments']

	cost_activity_params = {
		'created_date_gte': f"'{start_date.strftime('%m/%d/%Y')}'",
		'created_date_lt': f"'{end_date.strftime('%m/%d/%Y')}'",
		'application_names': f"'{formatted_applications}'",
		'$format': 'json'
	}
	cost_activity_response = get(cost_activity_url, params=cost_activity_params, **keyword_arguments)
	cost_activity_data = cost_activity_response.json()['d']

	if force_pi is None:
		latest_pis_params = {'$format': 'json'}
		latest_pis_response = get(project_lead_url, params=latest_pis_params, **keyword_arguments)
		latest_pis_data = latest_pis_response.json()['d']

	project_totals = {}
	application_totals = {}
	account_totals = {}
	user_pi_applications = list()
	# Construct a tree of account, application, project, and member total spending
	cost_activities_tree = {}
	for activity in cost_activity_data:
		if (project_id and activity['project_id'] != str(project_id)) or (account_id and activity['account_id'] != str(account_id)):
			continue
		project_totals.setdefault(activity['project_id'], 0)
		application_totals.setdefault(activity['application_id'], 0)
		account_totals.setdefault(activity['account_id'], 0)
		account_key = (activity['account_id'], activity['account_name'])
		application_key = (activity['application_id'], activity['application_name'])
		project_key = (activity['project_id'], activity['project_name'])
		user_key = (activity['member_id'], User.objects.filter(id__in=[activity['member_id']]).first())
		user_is_pi = is_user_pi(user, next((x for x in latest_pis_data if x['application_name'] == activity['application_name']), None)) if force_pi is None else True
		if user_is_pi:
			user_pi_applications.append(activity['application_id'])
		if user_is_pi or str(user.id) == activity['member_id']:
			cost_activities_tree.setdefault((activity['account_id'], activity['account_name']), {})
			cost_activities_tree[account_key].setdefault(application_key, {})
			cost_activities_tree[account_key][application_key].setdefault(project_key, {})
			cost_activities_tree[account_key][application_key][project_key].setdefault(user_key, 0)
			cost = -activity['cost'] if activity['activity_type'] == 'refund_activity' else activity['cost']
			cost_activities_tree[account_key][application_key][project_key][user_key] = cost_activities_tree[account_key][application_key][project_key][user_key] + cost
			project_totals[activity['project_id']] = project_totals[activity['project_id']] + cost
			application_totals[activity['application_id']] = application_totals[activity['application_id']] + cost
			account_totals[activity['account_id']] = account_totals[activity['account_id']] + cost
	dictionary['spending'] = {
		'activities': cost_activities_tree,
		'project_totals': project_totals,
		'application_totals': application_totals,
		'account_totals': account_totals,
		'user_pi_applications': user_pi_applications
	} if cost_activities_tree else {'activities': {}}
	return dictionary
