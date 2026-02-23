from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User, Request
from rest_framework import permissions, viewsets, generics, status
from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer, CreateRequestSerializer, ChangeRequestSerializer, \
    CreateFileSerializer


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


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    throttle_classes = [UserRateThrottle]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'completed']:
            return ChangeRequestSerializer
        return CreateRequestSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def attributed(self, request, pk=None):
        printing_request = self.get_object()
        printer_id = request.data.get('printer_id')
        if not printer_id:
            return Response({'error': 'printer_id is required'}, status=400)

        printing_request.status = Request.Status.PROCESSING
        printing_request.printer_id_id = printer_id
        printing_request.save()
        return Response({'status': 'print attributed, currently processing'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def completed(self, request, pk=None):
        printing_request = self.get_object()
        printing_request.status = Request.Status.COMPLETED
        printing_request.save()
        return Response({'status': 'print completed'})

class CreateFileView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateFileSerializer
    throttle_classes = [UserRateThrottle]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
