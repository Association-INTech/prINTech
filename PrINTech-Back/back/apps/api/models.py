import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=False, unique=True, null=False)
    credit = models.IntegerField(default=0)


class Filament(models.Model):

    class Type(models.TextChoices):
        PLA = 'PLA'
        PETG = 'PETG'

    class Color(models.TextChoices):
        RED = 'RED'
        GREEN = 'GREEN'
        YELLOW = 'YELLOW'
        BLUE = 'BLUE'
        MAGENTA = 'MAGENTA'
        WHITE = 'WHITE'
        BLACK = 'BLACK'
        PURPLE = 'PURPLE'
        BROWN = 'BROWN'
        GREY = 'GREY'
        ORANGE = 'ORANGE'

    colour = models.CharField(choices=Color.choices, max_length=25, null=False, blank=False)
    type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    quantity = models.PositiveIntegerField(default=0)


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

    class Type(models.TextChoices):
        CREALITY_K1C = 'CREALITY_K1C'
        SNAPMAKER_U1 = 'SNAPMAKER_U1'
        PRUSA_MK3 = 'PRUSA_MK3'
    type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
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
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.PENDING)

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
