import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=False, unique=True, null=False)
    credit = models.IntegerField(default=0)


class Filament(models.Model):

    class Type(models.TextChoices):
        PLA = 'PLA'
        REINFORCED_PLA = 'REINFORCED_PLA'
        PETG = 'PETG'
        ABS = 'ABS'
        TPE = 'TPE/TPU'

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
    user_id=models.ForeignKey(User, on_delete=models.CASCADE)
    filament_id=models.ManyToManyField(Filament)
    path = models.FileField(upload_to='uploads/%Y/%m/%d')
    number_of_printing = models.PositiveIntegerField(default=1)
    para_slicer =  models.JSONField(null=True, blank=True)


class Printer(models.Model):

    class Status(models.TextChoices):
        UP = 'UP'
        DOWN = 'DOWN'
        USED = 'USED'

    class Type(models.TextChoices):
        SLA = 'SLA/DLP/MSLA' #Resin
        SLS = 'SLS/MJF' #Powder
        FDM = 'FDM/FFF' #Filament
        MJP = 'MJP' #MultiJet Printing
        Binder_Jetting = 'Binder_Jetting'
        DMLS = 'DMLS/SLM' #Metal

    type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.DOWN)


class Request(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING'
        PROCESSING = 'PROCESSING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_id = models.ForeignKey(File, on_delete=models.CASCADE)
    printer_id = models.ForeignKey(Printer, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.PENDING)


class Operation(models.Model):

    class Type(models.TextChoices):
        CASH = 'CASH'
        CARD = 'CARD'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_beneficiary')
    agent_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operation_agent')
    created_at = models.DateTimeField(auto_now_add=True)
    operation_type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    amount = models.IntegerField(default=0)

