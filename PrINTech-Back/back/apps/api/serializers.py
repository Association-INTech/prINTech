from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User, Operation, Request, File, Filament, Printer
from django.db import transaction



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

    # noinspection PyMethodMayBeStatic
    def validate_password(self, password):
        validate_password(password)
        return password

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "credit", "is_staff", "profile_picture","role"]
        extra_kwargs = {
            "password": {"write_only": True},
            "credit": {"read_only": True},
            "is_staff": {"read_only": True},
            "role": {"read_only": True}
        }


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "credit", "is_staff", "is_active", "profile_picture", "role"]
        read_only_fields = ["id"]

    def validate_password(self, password):
        validate_password(password)
        return password

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
    class Meta:
        model = Operation
        fields = ['id', 'beneficiary', 'agent', 'amount', 'operation_type', 'comment', 'created_at','request'] 
        read_only_fields = ['agent', 'id', 'created_at']
        
    def create(self, validated_data):
        with transaction.atomic():
            beneficiary = validated_data['beneficiary']
            amount = validated_data['amount']
            if amount<0 and beneficiary.credit<-amount:
                raise serializers.ValidationError("Insufficient funds")
            beneficiary.credit += amount            
            beneficiary.save()
            return super().create(validated_data)
     
        
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["path", "number_of_printing", "filament", "para_slicer"]
        read_only_fields = ['id', 'user','status', 'printer', 'created_at', 'status']


class RequestSerializer(serializers.ModelSerializer):
    file = FileSerializer(many=False, read_only=True)
    path = serializers.FileField(write_only=True)
    number_of_printing = serializers.IntegerField(write_only=True, default=1)
    para_slicer = serializers.JSONField(write_only=True, required=False)
    filament = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Filament.objects.all(), required=True
    )
    class Meta:
        model = Request
        fields = ['id', 'user', 'file', 'printer', 'price', 'filament', 'comment', 'created_at','status',"path","number_of_printing", "para_slicer"] 
        read_only_fields = ['id', 'user','file', 'printer', 'price', 'created_at', 'status']
        
    def create(self, validated_data):
            path = validated_data.pop('path')
            number_of_printing = validated_data.pop('number_of_printing')
            para_slicer = validated_data.pop('para_slicer', {})
            filament = validated_data.pop('filament', None)

            new_file = File.objects.create(
                path=path,
                number_of_printing=number_of_printing,
                para_slicer=para_slicer,
                filament=filament
            )
            return Request.objects.create(file=new_file, **validated_data)
        
class FilamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filament
        fields = ['id', 'color', 'color_name', 'type', 'quantity']
        
class PrinterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = ['name', 'status']