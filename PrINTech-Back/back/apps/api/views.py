from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import User
from rest_framework import permissions, viewsets, generics, status
from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [UserRateThrottle]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({"Message": "Vous ne devez pas être authentifié."},status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = AccessToken.for_user(user)

        return Response(
            {
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserMeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            {"message": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK
        )

