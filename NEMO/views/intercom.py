import socket

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.shortcuts import render
from django.http import  HttpResponse

from NEMO.views.customization import get_customization
from NEMO.models import AreaAccessRecord, Area


def logout_annoucement(area):
    occupants = list(AreaAccessRecord.objects.filter(area__name=area.name, end=None, staff_charge=None).prefetch_related('customer__first_name').values_list('customer__first_name',flat=True))
    if len(occupants) > 1:
        num_occupants = str(len(occupants))
        occupants.insert(-1, 'and')
        occupants = ' '.join(occupants)
        message = f'Buddy System Alert: Only {num_occupants} lab members remain in the {area.name}. {occupants}, check in with your buddies.'
    else:
        message = f'Buddy System Warning: You are the only lab member in the {area.name}, {occupants[0]}. You may not work alone in the {area.name}.'
    auto_announcement(message)
    return

@login_required
@require_GET
@permission_required('NEMO.trigger_timed_services', raise_exception=True)
def scheduled_announcement(request, area_id):

    try:
        area = Area.objects.get(id=area_id)
        occupants_count = AreaAccessRecord.objects.filter(area__id=area_id, end=None, staff_charge=None).count()
        if occupants_count <= 3 and occupants_count > 0 and area.buddy_required():
            message = 'Buddy Alert: Please check in with others in the lab.'
            auto_announcement(message)
    except:
        pass
    return HttpResponse()


def auto_announcement(message):
    announce(str(message))
    return


@staff_member_required
@require_http_methods(['GET', 'POST'])
def test_announcement(request):
    ip = get_customization('audio_ip')
    port = int(get_customization('audio_port'))
    dictionary = {
        'ip': ip,
        'port': port,
    }
    if request.method == "POST":
        message = request.POST.get('msg', None)
        auto_announcement(message)
    return render(request, 'intercom.html', dictionary)


def announce(message):
    try:
        ip = get_customization('audio_ip')
        port = int(get_customization('audio_port'))
        if message:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip,port))
            sock.send(message.encode())
            sock.close()
    except:
        pass
    return
