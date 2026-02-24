from django.db.models.signals import post_delete
from django.dispatch import receiver
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User, Request, File, Printer
from rest_framework import viewsets, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer, CreateRequestSerializer, ChangeRequestSerializer, \
    CreateFileSerializer
from django.db import transaction

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [UserRateThrottle]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({"Message": "You need to be disconnected"},status=status.HTTP_403_FORBIDDEN)

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
            {"message": "Your password has been successfully modified."}, status=status.HTTP_200_OK
        )


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    authentication_classes = [TokenAuthentication, JWTAuthentication]
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Request.objects.all()
        return Request.objects.filter(file_id__user_id=user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'completed']:
            return ChangeRequestSerializer
        return CreateRequestSerializer


    def _assign_next_pending_request(self, printer):
        with transaction.atomic():
            next_request = Request.objects.filter(
                status=Request.Status.PENDING
            ).order_by('created_at').select_for_update(skip_locked=True).first()

            if next_request:
                next_request.printer_id = printer
                next_request.status = Request.Status.PROCESSING
                next_request.save()

                printer.status = Printer.Status.USED
                printer.save()
                return True
        return False


    def perform_create(self, serializer):
        new_request = serializer.save()
        with transaction.atomic():
            free_printer = Printer.objects.filter(status=Printer.Status.UP).first()
            if free_printer:
                self._assign_next_pending_request(free_printer)



    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def completed(self, request, pk=None):
        current_request = self.get_object()
        printer = current_request.printer_id

        if not request.user.is_bot :
            return Response({"error": "you are not a bot"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            current_request.status = Request.Status.COMPLETED
            current_request.save()

            if printer:
                printer.status = Printer.Status.UP
                printer.save()

        if printer:
            assigned = self._assign_next_pending_request(printer)
            if assigned:
                return Response({'status': 'completed and new request assigned'})

        return Response({'status': 'completed, printer is now idle'})

class CreateFileView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateFileSerializer
    throttle_classes = [UserRateThrottle]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FileViewSet(viewsets.ModelViewSet):
    serializer_class = CreateFileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        return File.objects.filter(user_id=self.request.user)

    @receiver(post_delete, sender=File)
    def submission_delete(sender, instance, **kwargs):
        instance.path.delete(False)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        has_active_print = instance.requests.filter(
            status__in=[Request.Status.PROCESSING, Request.Status.PENDING]
        ).exists()

        if has_active_print:
            return Response(
                {"error": "Impossible to delete this file, a request is being processed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

