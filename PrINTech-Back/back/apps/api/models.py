import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    
    class Priority(models.TextChoices):
        ADHERENT = 'ADHERENT', 'Adherent'
        ROBOTECH = 'ROBOTECH', 'Robotech'
        AUTOTECH = 'AUTOTECH', 'Autotech'
        DRONE = 'DRONE', 'Drone'
        BUREAU = 'BUREAU', 'Bureau'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=False, unique=True, null=False)
    credit = models.IntegerField(default=0)
    priority = models.CharField(choices=Priority.choices, max_length=25, null=False, blank=False, default=Priority.ADHERENT)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Filament(models.Model):

    class Type(models.TextChoices):
        PLA = 'PLA'
        PETG = 'PETG'

    color = models.CharField(
            max_length=7, 
            default='#ffffff',
            validators=[RegexValidator(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')]
        )
    color_name = models.TextField(null=False, blank=False)
    type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    quantity = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=0)


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filament=models.ForeignKey(Filament, on_delete=models.CASCADE, null=True)
    path = models.FileField(upload_to='uploads/%Y/%m/%d')
    number_of_printing = models.PositiveIntegerField(default=1)
    para_slicer =  models.JSONField(null=True, blank=True)


class Printer(models.Model):

    class Status(models.TextChoices):
        UP = 'UP'
        DOWN = 'DOWN'
        USED = 'USED'

    class Name(models.TextChoices):
        CREALITY_K1C = 'CREALITY_K1C'
        SNAPMAKER_U1 = 'SNAPMAKER_U1'
        PRUSA_MK3 = 'PRUSA_MK3'
        
    name = models.CharField(primary_key=True,choices=Name.choices, max_length=25, null=False, blank=False)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.DOWN)



class Request(models.Model):

    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT'
        PENDING = 'PENDING'
        PRINTING = 'PRINTING'
        AWAITING_PICKUP = 'AWAITING_PICKUP'
        PICKED_UP = 'PICKED_UP'
        FAILED = 'FAILED'
        CANCELED = 'CANCELED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, null=True)
    price = models.PositiveIntegerField(default=0)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.SUBMITTED)

    @property
    def is_paid(self):
        return hasattr(self, 'operation')

class Operation(models.Model):

    class Type(models.TextChoices):
        CASH = 'CASH'
        CARD = 'CARD'
        PAYMENT = 'PAYMENT'
        REFUND = 'REFUND'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_beneficiary')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_agent')
    created_at = models.DateTimeField(auto_now_add=True)
    operation_type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    amount = models.IntegerField(default=0)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, null=True)
