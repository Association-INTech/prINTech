from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import User, Operation, Request
from rest_framework import permissions, viewsets, mixins, generics, status, serializers
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework.throttling import UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer, OperationSerializer, RequestSerializer
from django.db import transaction

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

class OperationView(mixins.ListModelMixin, 
                           mixins.RetrieveModelMixin, 
                           viewsets.GenericViewSet):
    serializer_class = OperationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Operation.objects.filter(beneficiary=self.request.user)

class AdminOperationView(mixins.CreateModelMixin, 
                            mixins.ListModelMixin, 
                            mixins.RetrieveModelMixin, 
                            viewsets.GenericViewSet):
    serializer_class = OperationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Operation.objects.all()

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)
                
class RequestView(mixins.CreateModelMixin, 
                       mixins.ListModelMixin, 
                       mixins.RetrieveModelMixin, 
                       viewsets.GenericViewSet):
    serializer_class = RequestSerializer
    permission_classes=[IsAuthenticated]
    def get_queryset(self):
        return Request.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='SUBMITTED')
        
class AdminRequestView(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequestSerializer
    permission_classes=[IsAdminUser]
    queryset = Request.objects.all()
    
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk):
        print_request = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            statuses = Request.Status.values
            current_status = str(print_request.status)
            current_index = statuses.index(current_status)
            
            #Cannot auto change to ERROR and CANCELED
            ERROR_STATUS_COUNT = 2
            if current_index < len(statuses) - ERROR_STATUS_COUNT - 1:
                    new_status = statuses[current_index + 1]
            else:
                return Response(
                    {'error': 'Already Completed.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )


        print_request.status = new_status
        print_request.save() 
        
        serializer = self.get_serializer(print_request)
        return Response(serializer.data)