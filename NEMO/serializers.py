from rest_framework.serializers import ModelSerializer

from NEMO.models import User, Project, Account, Reservation, AreaAccessRecord, UsageEvent, Task, TaskHistory, Sensor, ScheduledOutage, Tool, Interlock, StockroomWithdraw, StockroomItem, UserChemical


class UserSerializer(ModelSerializer):
	class Meta:
		model = User
		fields = ('id', 'first_name', 'last_name', 'username', 'email', 'physical_access_levels', 'type', 'date_joined', 'access_expiration')


class ProjectSerializer(ModelSerializer):
	class Meta:
		model = Project
		fields = ('id', 'name', 'application_identifier', 'active', 'account')


class AccountSerializer(ModelSerializer):
	class Meta:
		model = Account
		fields = ('id', 'name', 'active')


class ToolSerializer(ModelSerializer):
	class Meta:
		model = Tool
		fields = '__all__'


class ReservationSerializer(ModelSerializer):
	class Meta:
		model = Reservation
		fields = '__all__'


class UsageEventSerializer(ModelSerializer):
	class Meta:
		model = UsageEvent
		fields = '__all__'


class AreaAccessRecordSerializer(ModelSerializer):
	class Meta:
		model = AreaAccessRecord
		fields = '__all__'


class TaskHistorySerializer(ModelSerializer):
	class Meta:
		model = TaskHistory
		fields = '__all__'


class TaskSerializer(ModelSerializer):
	history = TaskHistorySerializer(many=True, read_only=True)

	class Meta:
		model = Task
		fields = '__all__'


class ScheduledOutageSerializer(ModelSerializer):
	class Meta:
		model = ScheduledOutage
		fields = '__all__'


class InterlockSerializer(ModelSerializer):
	class Meta:
		model = Interlock
		fields = '__all__'


class SensorSerializer(ModelSerializer):
	class Meta:
		model = Sensor
		fields = '__all__'


class StockroomWithdrawSerializer(ModelSerializer):
	class Meta:
		model = StockroomWithdraw
		fields = '__all__'


class StockroomItemSerializer(ModelSerializer):
	class Meta:
		model = StockroomItem
		fields = '__all__'


class UserChemicalSerializer(ModelSerializer):
	class Meta:
		model = UserChemical
		fields = '__all__'
