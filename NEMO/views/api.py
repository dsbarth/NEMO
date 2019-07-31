from rest_framework.viewsets import ReadOnlyModelViewSet

from NEMO.filters import ReservationFilter, UsageEventFilter, AreaAccessRecordFilter, UserFilter
from NEMO.models import User, Project, Account, Reservation, UsageEvent, AreaAccessRecord, Task, ScheduledOutage, Tool, Interlock, Sensor, StockroomWithdraw, StockroomItem, UserChemical
from NEMO.serializers import UserSerializer, ProjectSerializer, AccountSerializer, ReservationSerializer, UsageEventSerializer, AreaAccessRecordSerializer, TaskSerializer, ScheduledOutageSerializer, SensorSerializer, ToolSerializer, InterlockSerializer, StockroomWithdrawSerializer, StockroomItemSerializer, UserChemicalSerializer


class UserViewSet(ReadOnlyModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	filter_class = UserFilter


class ProjectViewSet(ReadOnlyModelViewSet):
	queryset = Project.objects.all()
	serializer_class = ProjectSerializer


class AccountViewSet(ReadOnlyModelViewSet):
	queryset = Account.objects.all()
	serializer_class = AccountSerializer


class ToolViewSet(ReadOnlyModelViewSet):
	queryset = Tool.objects.all()
	serializer_class = ToolSerializer


class ReservationViewSet(ReadOnlyModelViewSet):
	queryset = Reservation.objects.all()
	serializer_class = ReservationSerializer
	filter_class = ReservationFilter


class UsageEventViewSet(ReadOnlyModelViewSet):
	queryset = UsageEvent.objects.all()
	serializer_class = UsageEventSerializer
	filter_class = UsageEventFilter


class AreaAccessRecordViewSet(ReadOnlyModelViewSet):
	queryset = AreaAccessRecord.objects.all()
	serializer_class = AreaAccessRecordSerializer
	filter_class = AreaAccessRecordFilter


class TaskViewSet(ReadOnlyModelViewSet):
	queryset = Task.objects.all()
	serializer_class = TaskSerializer


class ScheduledOutageViewSet(ReadOnlyModelViewSet):
	queryset = ScheduledOutage.objects.all()
	serializer_class = ScheduledOutageSerializer


class InterlockViewSet(ReadOnlyModelViewSet):
	queryset = Interlock.objects.all()
	serializer_class = InterlockSerializer


class StockroomWithdrawViewSet(ReadOnlyModelViewSet):
	queryset = StockroomWithdraw.objects.all()
	serializer_class = StockroomWithdrawSerializer


class StockroomItemsViewSet(ReadOnlyModelViewSet):
	queryset = StockroomItem.objects.all()
	serializer_class = StockroomItemSerializer


class SensorViewSet(ReadOnlyModelViewSet):
	queryset = Sensor.objects.all()
	serializer_class = SensorSerializer


class UserChemicalViewSet(ReadOnlyModelViewSet):
	queryset = UserChemical.objects.all()
	serializer_class = UserChemicalSerializer
