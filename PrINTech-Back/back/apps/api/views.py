from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import User, Operation, Request, Filament, Printer
from django.db.models import Case, When, IntegerField, Value
from rest_framework import permissions, viewsets, mixins, generics, status, serializers
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser
from rest_framework.throttling import UserRateThrottle
from .serializers import UserSerializer, ChangePasswordSerializer, OperationSerializer, RequestSerializer,FilamentSerializer, PrinterSerializer
from .serializers import AdminUserSerializer
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


class UserMeView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    def destroy(self, request, *args, **kwargs):
        """Deletes ONLY profile picture, not the user account."""
        user = self.get_object()
        if user.profile_picture:
            user.profile_picture.delete(save=False) 
            user.profile_picture = None
            user.save()
            return Response({"message": "Photo de profil supprimée avec succès."}, status=status.HTTP_200_OK)
        return Response({"error": "Aucune photo de profil à supprimer."}, status=status.HTTP_400_BAD_REQUEST)

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

    @transaction.atomic
    @action(detail=True, methods=['post'])
    def relaunch(self, request, pk=None):
        previous_request = self.get_object()

        if previous_request.file is None:
            return Response(
                {"error": "Cannot relaunch a request without file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        relaunched_request = Request.objects.create(
            user=request.user,
            file=previous_request.file,
            printer=None,
            comment=previous_request.comment,
            status='SUBMITTED',
        )

        serializer = self.get_serializer(relaunched_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        print_request = self.get_object()

        if print_request.status != 'AWAITING_PAYMENT':
            return Response(
                {"error": "Request not awaiting payment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        price = print_request.price
        if price <= 0:
            return Response(
                {"error": "Request price is not set."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = {
                "beneficiary": request.user.id,
                "amount": -price,
                "operation_type": "PAYMENT",
                "request": print_request.id
            }
        
        serializer = OperationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(agent=request.user)
            print_request.status = 'PENDING'
            print_request.save()
            return Response(status=201)
        return Response(serializer.errors, status=400)
    
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        print_request = self.get_object()
        
        allowed_cancel = ['SUBMITTED','AWAITING_PAYMENT', 'PENDING']
        
        if print_request.status not in allowed_cancel:
            return Response(
                {"error": f"Cannot cancel for status: {print_request.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if print_request.status == 'PENDING':
            #Operation default related_name: `operation_set`
            payments = print_request.operation_set.filter(
                operation_type=Operation.Type.PAYMENT
            )
            
            if payments.count() > 1:
                return Response(
                    {"error": "Cannot refund"},
                    status=status.HTTP_409_CONFLICT
                )
            elif payments.count() == 1:
                payment = payments.first()
                refund_amount = abs(payment.amount)

                data = {
                    "beneficiary": print_request.user.id,
                    "amount": refund_amount,
                    "operation_type": "REFUND",
                    "request": print_request.id,
                    "comment": f"Refund for cancellation of request {print_request.id}"
                }

                serializer = OperationSerializer(data=data)
                if serializer.is_valid():
                    serializer.save(agent=request.user)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        

        print_request.status = 'CANCELED'
        print_request.save()
        
        return Response({"status": "Request canceled successfully"}, status=status.HTTP_200_OK)
    
class AdminRequestView(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequestSerializer
    permission_classes=[IsAdminUser]

    def get_queryset(self):
        # BUREAU highest (0), project types equal (1), ADHERENT lowest (2)
        qs = Request.objects.all().annotate(
            priority_rank=Case(
                When(user__role='BUREAU', then=Value(0)),
                When(user__role='ROBOTECH', then=Value(1)),
                When(user__role='AUTOTECH', then=Value(1)),
                When(user__role='DRONE', then=Value(1)),
                When(user__role='ADHERENT', then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('priority_rank', '-created_at')
        return qs
    
    @transaction.atomic
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk):
        print_request = self.get_object()
        new_status = request.data.get('status')
        price = request.data.get('price')
        current_status = str(print_request.status)
        statuses = Request.Status.values

        if current_status == Request.Status.SUBMITTED and new_status and new_status != Request.Status.AWAITING_PAYMENT:
            return Response(
                {'error': 'New requests must move to awaiting payment first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_status == Request.Status.AWAITING_PAYMENT:
            if not new_status:
                return Response(
                    {'error': 'Request is waiting for user payment.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if new_status != Request.Status.AWAITING_PAYMENT:
                return Response(
                    {'error': 'Request must be paid before advancing status.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if current_status in [Request.Status.SUBMITTED, Request.Status.AWAITING_PAYMENT] and new_status == Request.Status.AWAITING_PAYMENT:
            if price is None:
                return Response(
                    {'error': 'A price is required before setting awaiting payment.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                price = int(price)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid price.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if price <= 0:
                return Response(
                    {'error': 'Price must be greater than zero.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print_request.price = price

        if not new_status:
            current_index = statuses.index(current_status)

            if current_status == Request.Status.SUBMITTED:
                new_status = Request.Status.AWAITING_PAYMENT
            else:
                # Cannot autochange to ERROR/CANCELED.
                ERROR_STATUS_COUNT = 2
                if current_index < len(statuses) - ERROR_STATUS_COUNT - 1:
                    new_status = statuses[current_index + 1]
                else:
                    return Response(
                        {'error': 'Already Completed.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if new_status == Request.Status.AWAITING_PAYMENT:
                if price is None:
                    return Response(
                        {'error': 'A price is required before setting awaiting payment.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    price = int(price)
                except (TypeError, ValueError):
                    return Response(
                        {'error': 'Invalid price.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if price <= 0:
                    return Response(
                        {'error': 'Price must be greater than zero.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                print_request.price = price

        if new_status not in statuses:
            return Response(
                {'error': f'Invalid status: {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )


        print_request.status = new_status
        print_request.save() 
        
        serializer = self.get_serializer(print_request)
        return Response(serializer.data)


class AdminUserView(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('email')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    
    
class FilamentView(viewsets.ReadOnlyModelViewSet):
    queryset = Filament.objects.all()
    serializer_class = FilamentSerializer
    permission_classes = [permissions.AllowAny]

class AdminFilamentView(viewsets.ModelViewSet):
    queryset = Filament.objects.all()
    serializer_class = FilamentSerializer
    permission_classes = [permissions.IsAdminUser]
    
class PrinterView(viewsets.ReadOnlyModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [permissions.AllowAny]
 
class AdminPrinterView(mixins.UpdateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [permissions.IsAdminUser]