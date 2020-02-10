from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range
from decimal import *

from datetime import timedelta, date
from time import sleep
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST, require_GET, require_http_methods

from NEMO.utilities import parse_start_and_end_date, month_list, get_month_timeframe
from NEMO.models import User, UserType, AreaAccessRecord, Account, Project, StockroomWithdraw, StaffCharge
from NEMO.views.customization import get_customization

#@staff_member_required(login_url=None)
#@require_GET
def get_billing_data(start, end):
	billing_result = []
	undergrad_rate = UserType.objects.get(name='Undergraduate').daily_rate
	#daily_rate = {'Internal - Full':135, 'Internal - Unlimited':0, 'Internal - SMP':67.5, 'Internal - Packaging':67.5, 'External Academic':220,'Industrial':0,'Undergraduate':45}

	#staff_charge_rate = {'Internal - Full':80, 'Internal - Unlimited':80, 'Internal - SMP':80, 'Internal - Packaging':80, 'External Academic':130,'Industrial':480,'Undergraduate':80}
	user_exclude = [1,3,7,8]
	projects_to_exclude = []
	exclude=get_customization('exclude_from_billing')
	if exclude:
		projects_to_exclude = [int(s) for s in exclude.split() if s.isdigit()]
	users = User.objects.all().exclude(type__in=user_exclude).order_by('type', 'last_name')
	for user in users:
		billable_days = 0
		try:
			user_access = AreaAccessRecord.objects.filter(customer=user, end__gte=start, end__lt=end, staff_charge=None).exclude(project__id__in=projects_to_exclude).order_by('start')
			for index, access_event in enumerate(user_access):
				start_date = timezone.localtime(access_event.start).date()
				end_date = timezone.localtime(access_event.end).date()
				dt = end_date - start_date
				days = dt.days
				if index == 0:
					billable_days += days + 1
				else:
					last_access = user_access[index-1]
					if timezone.localtime(last_access.end).date() == start_date:
						billable_days += days
					else:
						billable_days += days + 1
		except:
			pass
		stockroom_bill = 0
		try:
			stockroom_withdraws = StockroomWithdraw.objects.filter(customer=user, date__range=(start, end))
			for purchase in stockroom_withdraws:
				stockroom_bill += purchase.stock.cost*purchase.quantity
		except:
			pass
		staff_charge_bill = 0
		try:
			staff_charge = StaffCharge.objects.filter(customer=user, end__gte=start, end__lt=end, validated=True)
			for charge in staff_charge:
				chargetime = charge.end-charge.start
				staff_charge_bill += round(Decimal(chargetime.total_seconds()/3600)*user.type.staff_rate,2)
		except:
			pass
		name = user.last_name + ", " + user.first_name
		usage_bill=0
		try:
			principal_inv = user.active_projects().exclude(id__in=projects_to_exclude).values_list('account__name', flat=True)[0]
		except:
			principal_inv = "unknown"
		if user.type.name == 'Internal - Unlimited':
			usage_bill = user.type.daily_rate
		elif user.type.name == 'Internal - Full' or user.type.name == 'Internal - Packaging' or user.type.name == 'Internal - SMP':
			if billable_days > 10:
				usage_bill = 10*user.type.daily_rate+(billable_days-10)*undergrad_rate
			else:
				usage_bill = billable_days*user.type.daily_rate
		else:
			usage_bill = billable_days*user.type.daily_rate
		user_billing = {'username': user.username, 'name': name, 'email': user.email, 'PI': principal_inv, 'user_type': user.type.name, 'billable_days': billable_days, 'rate':user.type.daily_rate, 'usage_bill': usage_bill, 'stockroom_bill': stockroom_bill, 'staff_charge_bill': staff_charge_bill, 'total_bill': usage_bill+staff_charge_bill+stockroom_bill}
		billing_result.append(user_billing)

	return billing_result

@staff_member_required(login_url=None)
@require_GET
def billing(request):
	""" Presents a page that displays billing. """
	dictionary = {}
	try:
		start, end = parse_start_and_end_date(request.GET['start'], request.GET['end'])
		dictionary['start'] = start
		dictionary['end'] = end
		dictionary['billing_result'] = get_billing_data(start, end)
	except:
		pass
	return render(request, 'billing.html', dictionary)


@staff_member_required(login_url=None)
@require_GET
def billingxls(request):
	dictionary = {}
	try:
		start, end = parse_start_and_end_date(request.GET['start'], request.GET['end'])
		fn = "billing_" + start.strftime("%Y%m%d") + "_" + end.strftime("%Y%m%d") + ".xlsx"
		billing_result = get_billing_data(start, end)
		unlimited_rate = UserType.objects.get(name='Internal - Unlimited').daily_rate
		undergrad_rate = UserType.objects.get(name='Undergraduate').daily_rate
		response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename = "%s"' % fn
		book = Workbook(response, {'in_memory': True})
		sheet = book.add_worksheet('billing')
		bold = book.add_format()
		bold.set_bold()
		money=book.add_format()
		money.set_num_format('$0.00')
		redgreen = book.add_format()
		redgreen.set_num_format('[Green]General;[Red]-General;General')
		rgmoney = book.add_format()
		rgmoney.set_num_format('[Green]$0.00;[Red]-$0.00;$0.00')
		fields = ['Username', 'Name', 'Email', 'PI', 'Type', 'Billable Days', 'Adjustments', 'Rate', 'Usage Bill', 'Stockroom Bill', 'Staff Charge Bill', 'Final Adjustments', 'Total Bill']
		sheet.write_row('A1', fields, bold)
		iter = 1
		for r in billing_result:
			if not r['billable_days'] == 0 or not r['total_bill'] == 0:
				days_cell = xl_rowcol_to_cell(iter,5)
				adj_cell = xl_rowcol_to_cell(iter,7)
				if r['user_type'] == 'Internal - Unlimited':
					usage_eq = unlimited_rate
				elif r['user_type'] == 'Internal - Full'or r['user_type'] == 'Internal - Packaging' or r['user_type'] == 'Internal - SMP':
					usage_eq = f'=min({xl_rowcol_to_cell(iter,5)}+{xl_rowcol_to_cell(iter,6)},10)*{xl_rowcol_to_cell(iter,7)}+max(-10+{xl_rowcol_to_cell(iter,5)}+{xl_rowcol_to_cell(iter,6)},0)*{undergrad_rate}'
				else:
					usage_eq = f'=({xl_rowcol_to_cell(iter,5)}+{xl_rowcol_to_cell(iter,6)})*{xl_rowcol_to_cell(iter,7)}'
				total_eq = f'=sum({xl_range(iter, 8, iter, 11)})'
				row = [r['username'], r['name'], r['email'], r['PI'], r['user_type'], r['billable_days'], "", r['rate'], usage_eq, r['stockroom_bill'], r['staff_charge_bill'], "", total_eq]
				sheet.write_row(iter,0,row)
				iter +=1
		sheet.set_column('H:M', None, money)
		sheet.set_column('G:G', None, redgreen)
		sheet.set_column('L:L', None, rgmoney)
		book.close()
		return response
	except:
		return render(request, 'billing.html', dictionary)
