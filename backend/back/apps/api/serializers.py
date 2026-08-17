import json
import struct
from pathlib import Path

from django.conf import settings

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.urls import reverse
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from .models import User, Operation, Request, File, Filament, Printer


MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
MAX_PRINT_FILE_SIZE = 100 * 1024 * 1024
MAX_NUMBER_OF_PRINTS = 100
MAX_PARA_SLICER_BYTES = 10 * 1024
MAX_COMMENT_LENGTH = 2000
ALLOWED_PROFILE_PICTURE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_PRINT_EXTENSIONS = {'.stl'}


def normalize_email(email):
    return email.strip().lower()


def validate_unique_email(email, *, instance=None):
    normalized = normalize_email(email)
    qs = User.objects.filter(email__iexact=normalized)
    if instance is not None:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise serializers.ValidationError('A user with this email already exists.')
    return normalized


def validate_upload(uploaded_file, *, allowed_extensions, max_size, label):
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in allowed_extensions:
        raise serializers.ValidationError(
            f"Invalid {label} extension. Allowed extensions: {', '.join(sorted(allowed_extensions))}."
        )
    if uploaded_file.size > max_size:
        max_size_mb = max_size // (1024 * 1024)
        raise serializers.ValidationError(f"{label.capitalize()} must be {max_size_mb} MB or less.")
    return uploaded_file


def reset_upload(uploaded_file):
    try:
        uploaded_file.seek(0)
    except (AttributeError, OSError):
        pass


def validate_image_upload(uploaded_file):
    validate_upload(
        uploaded_file,
        allowed_extensions=ALLOWED_PROFILE_PICTURE_EXTENSIONS,
        max_size=MAX_PROFILE_PICTURE_SIZE,
        label='profile picture',
    )
    try:
        image = Image.open(uploaded_file)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise serializers.ValidationError('Invalid profile picture content.') from exc
    finally:
        reset_upload(uploaded_file)
    return uploaded_file


def looks_like_stl(uploaded_file):
    reset_upload(uploaded_file)
    head = uploaded_file.read(512)
    reset_upload(uploaded_file)

    if head.lstrip().lower().startswith(b'solid'):
        try:
            uploaded_file.seek(max(uploaded_file.size - 1024, 0))
            tail = uploaded_file.read(1024).lower()
        finally:
            reset_upload(uploaded_file)
        return b'endsolid' in tail

    if uploaded_file.size < 84:
        return False

    try:
        uploaded_file.seek(80)
        triangle_count_bytes = uploaded_file.read(4)
    finally:
        reset_upload(uploaded_file)

    if len(triangle_count_bytes) != 4:
        return False

    triangle_count = struct.unpack('<I', triangle_count_bytes)[0]
    return 84 + triangle_count * 50 == uploaded_file.size


def validate_stl_upload(uploaded_file):
    validate_upload(
        uploaded_file,
        allowed_extensions=ALLOWED_PRINT_EXTENSIONS,
        max_size=MAX_PRINT_FILE_SIZE,
        label='print file',
    )
    if not looks_like_stl(uploaded_file):
        raise serializers.ValidationError('Invalid STL file content.')
    return uploaded_file


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, password):
        user = self.context["request"].user
        if not user.check_password(password):
            raise serializers.ValidationError("Wrong password")
        return password

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def validate_new_password(self, password):
        validate_password(password, user=self.context["request"].user)
        return password

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
        )
        return user

    def validate_email(self, email):
        return validate_unique_email(email, instance=getattr(self, 'instance', None))

    # noinspection PyMethodMayBeStatic
    def validate_password(self, password):
        validate_password(password)
        return password

    # noinspection PyMethodMayBeStatic
    def validate_profile_picture(self, profile_picture):
        return validate_image_upload(profile_picture)

    def update(self, instance, validated_data):
        # Password changes must go through ChangePasswordView so the old password is checked.
        validated_data.pop('password', None)
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "credit", "is_staff", "profile_picture","role"]
        extra_kwargs = {
            "password": {"write_only": True, "required": True},
            "credit": {"read_only": True},
            "is_staff": {"read_only": True},
            "role": {"read_only": True}
        }


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    def validate_email(self, email):
        return validate_unique_email(email, instance=getattr(self, 'instance', None))

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "credit", "is_staff", "is_active", "profile_picture", "role"]
        read_only_fields = ["id", "credit"]

    def validate_password(self, password):
        validate_password(password)
        return password

    # noinspection PyMethodMayBeStatic
    def validate_profile_picture(self, profile_picture):
        return validate_image_upload(profile_picture)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class OperationSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = Operation
        fields = ['id', 'beneficiary', 'agent', 'amount', 'operation_type', 'comment', 'created_at','request'] 
        read_only_fields = ['agent', 'id', 'created_at']

    def validate(self, attrs):
        operation_type = attrs.get('operation_type')
        amount = attrs.get('amount')
        request_obj = attrs.get('request')
        beneficiary = attrs.get('beneficiary')

        if amount is None or amount == 0:
            raise serializers.ValidationError('Operation amount cannot be zero.')

        if self.context.get('manual_admin_operation') and operation_type in [Operation.Type.PAYMENT, Operation.Type.REFUND]:
            raise serializers.ValidationError('Manual operations must be CASH or CARD.')

        if operation_type in [Operation.Type.CASH, Operation.Type.CARD] and amount <= 0:
            raise serializers.ValidationError('CASH and CARD operations must credit a positive amount.')

        if self.context.get('manual_admin_operation') and operation_type in [Operation.Type.CASH, Operation.Type.CARD]:
            max_amount = settings.MAX_MANUAL_CREDIT_OPERATION_AMOUNT
            if amount > max_amount:
                raise serializers.ValidationError(
                    f'Manual credit operations are limited to {max_amount} credits.'
                )

        if operation_type == Operation.Type.PAYMENT:
            if request_obj is None:
                raise serializers.ValidationError('PAYMENT operations must be linked to a request.')
            if amount >= 0:
                raise serializers.ValidationError('PAYMENT operations must debit a negative amount.')

        if operation_type == Operation.Type.REFUND:
            if request_obj is None:
                raise serializers.ValidationError('REFUND operations must be linked to a request.')
            if amount <= 0:
                raise serializers.ValidationError('REFUND operations must credit a positive amount.')

        if request_obj is not None and beneficiary is not None and request_obj.user_id != beneficiary.id:
            raise serializers.ValidationError('Operation beneficiary must match the request owner.')

        if request_obj is not None and operation_type in [Operation.Type.PAYMENT, Operation.Type.REFUND]:
            if Operation.objects.filter(request=request_obj, operation_type=operation_type).exists():
                raise serializers.ValidationError(f'{operation_type} operation already exists for this request.')

        return attrs
        
    def create(self, validated_data):
        try:
            with transaction.atomic():
                beneficiary = User.objects.select_for_update().get(pk=validated_data['beneficiary'].pk)
                validated_data['beneficiary'] = beneficiary
                amount = validated_data['amount']
                if amount < 0 and beneficiary.credit < -amount:
                    raise serializers.ValidationError("Insufficient funds")
                beneficiary.credit += amount
                beneficiary.save(update_fields=['credit'])
                return super().create(validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError('Duplicate operation for this request.') from exc
     
        
class FileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    path = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["id", "path", "download_url", "number_of_printing", "filament", "para_slicer"]
        read_only_fields = ["id", "path", "download_url"]

    def get_path(self, obj) -> str | None:
        return Path(obj.path.name).name if obj.path else None

    def get_download_url(self, obj) -> str:
        return reverse('file-download', args=[obj.id])


class RequestSerializer(serializers.ModelSerializer):
    file = FileSerializer(many=False, read_only=True)
    path = serializers.FileField(write_only=True)
    number_of_printing = serializers.IntegerField(
        write_only=True,
        default=1,
        min_value=1,
        max_value=MAX_NUMBER_OF_PRINTS,
    )
    para_slicer = serializers.JSONField(write_only=True, required=False)
    filament = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Filament.objects.all(), required=True
    )
    # noinspection PyMethodMayBeStatic
    def validate_path(self, path):
        return validate_stl_upload(path)

    # noinspection PyMethodMayBeStatic
    def validate_comment(self, comment):
        if comment and len(comment) > MAX_COMMENT_LENGTH:
            raise serializers.ValidationError(f'Comment must be {MAX_COMMENT_LENGTH} characters or less.')
        return comment

    # noinspection PyMethodMayBeStatic
    def validate_para_slicer(self, para_slicer):
        try:
            encoded = json.dumps(para_slicer, separators=(',', ':'), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError('Invalid slicer parameters.') from exc
        if len(encoded.encode('utf-8')) > MAX_PARA_SLICER_BYTES:
            raise serializers.ValidationError('Slicer parameters are too large.')
        return para_slicer

    def validate(self, attrs):
        filament = attrs.get('filament')
        number_of_printing = attrs.get('number_of_printing', 1)
        if filament is not None:
            if filament.price <= 0:
                raise serializers.ValidationError({'filament': 'Selected filament has no valid price.'})
            if filament.quantity < number_of_printing:
                raise serializers.ValidationError({'filament': 'Not enough filament stock.'})
        return attrs

    class Meta:
        model = Request
        fields = ['id', 'user', 'file', 'printer', 'price', 'filament', 'comment', 'created_at','status',"path","number_of_printing", "para_slicer"] 
        read_only_fields = ['id', 'user','file', 'printer', 'price', 'created_at', 'status']
        
    def create(self, validated_data):
        path = validated_data.pop('path')
        number_of_printing = validated_data.pop('number_of_printing')
        para_slicer = validated_data.pop('para_slicer', {})
        filament = validated_data.pop('filament', None)
        new_file = None

        try:
            new_file = File.objects.create(
                path=path,
                number_of_printing=number_of_printing,
                para_slicer=para_slicer,
                filament=filament
            )
            return Request.objects.create(file=new_file, **validated_data)
        except Exception:
            if new_file and new_file.path:
                new_file.path.delete(save=False)
            raise
        
class FilamentSerializer(serializers.ModelSerializer):
    def validate_price(self, price):
        if price <= 0:
            raise serializers.ValidationError('Filament price must be positive.')
        return price

    class Meta:
        model = Filament
        fields = ['id', 'color', 'color_name', 'type', 'quantity', 'price']
        
class PrinterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = ['name', 'status']