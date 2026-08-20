import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.core.validators import RegexValidator


class User(AbstractUser):
    
    class Role(models.TextChoices):
        ADHERENT = 'ADHERENT', 'Adherent'
        ROBOTECH = 'ROBOTECH', 'Robotech'
        AUTOTECH = 'AUTOTECH', 'Autotech'
        DRONE = 'DRONE', 'Drone'
        BUREAU = 'BUREAU', 'Bureau'
    
    def profile_pic_path(instance, filename):
        ext = filename.split('.')[-1]
        return f'profile_pics/{instance.id}.{ext}'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=False, unique=True, null=False)
    credit = models.IntegerField(default=0)
    role = models.CharField(choices=Role.choices, max_length=25, null=False, blank=False, default=Role.ADHERENT)
    profile_picture = models.ImageField(upload_to=profile_pic_path, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(Lower('email'), name='api_user_email_lower_unique'),
            models.CheckConstraint(condition=Q(credit__gte=0), name='api_user_credit_non_negative'),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

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
    price = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=1), name='api_filament_price_positive'),
        ]


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filament=models.ForeignKey(Filament, on_delete=models.PROTECT, null=True, blank=True)
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
        REFUNDED = 'REFUNDED'
        CANCELED = 'CANCELED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user=models.ForeignKey(User, on_delete=models.PROTECT)
    file = models.ForeignKey(File, on_delete=models.PROTECT, null=True)
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True)
    price = models.PositiveIntegerField(default=0)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=Status.choices, max_length=25, null=False, blank=False, default=Status.SUBMITTED)

    @property
    def is_paid(self):
        return self.operation_set.filter(operation_type=Operation.Type.PAYMENT).exists()

class Operation(models.Model):

    class Type(models.TextChoices):
        CASH = 'CASH'
        CARD = 'CARD'
        PAYMENT = 'PAYMENT'
        REFUND = 'REFUND'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(User, on_delete=models.PROTECT, related_name='operation_beneficiary')
    agent = models.ForeignKey(User, on_delete=models.PROTECT, related_name='operation_agent')
    created_at = models.DateTimeField(auto_now_add=True)
    operation_type = models.CharField(choices=Type.choices, max_length=25, null=False, blank=False)
    comment = models.TextField(null=True, blank=True)
    amount = models.IntegerField(default=0)
    request = models.ForeignKey(Request, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['request'],
                condition=Q(operation_type='PAYMENT', request__isnull=False),
                name='api_operation_one_payment_per_request',
            ),
            models.UniqueConstraint(
                fields=['request'],
                condition=Q(operation_type='REFUND', request__isnull=False),
                name='api_operation_one_refund_per_request',
            ),
        ]


class AdminActionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_action_logs')
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=120)
    target_id = models.CharField(max_length=120)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
