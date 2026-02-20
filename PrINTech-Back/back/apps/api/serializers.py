from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.fields import UUIDField

from .models import User, Request, File


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
        fields = ["id", "username", "password", "email"]
        extra_kwargs = {"password": {"write_only": True}}



class CreateFileSerializer(serializers.ModelSerializer):
    requests = serializers.PrimaryKeyRelatedField(many=False, pk_field=UUIDField(format='hex'), required=False, queryset=Request.objects.all())
    filaments = serializers.PrimaryKeyRelatedField(many=True, queryset=File.objects.all())

    class Meta:
        model = File
        fields = [
            "user_id",
            "path",
            "number_of_printing",
            "filaments",
            "requests",
            "para_slicer",
        ]

    def validate(self, data):
        user = self.context["request"].user
        path = data["path"]

        if File.objects.filter(path=path, user_id=user).exists():
            raise serializers.ValidationError("File already exists")

        return data


class CreateRequestSerializer(serializers.ModelSerializer):


    class Meta:
        model = Request
        fields = ["file_id", "printer_id", "created_at"]
        extra_kwargs = {"created_at": {"read_only": True}}

    def validate(self, data):
        pass