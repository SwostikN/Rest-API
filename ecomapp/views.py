from rest_framework.generics import RetrieveUpdateDestroyAPIView,CreateAPIView,ListCreateAPIView
from rest_framework.views import APIView
from .models import OrderCompanyStatus,CustomUser,Product,Order,OrderItem,CartItem,Cart,Company
from .serializers import OrderCompanyStatusSerializer,AdminOrderSerializer,OrderItemSerializer,InvitationSerializer,CompanySerializer,UserSerializer,UserLoginSerializer,ProductSerializer,UserOrderSerializer,CartItemSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .permissions import IsOwner,IsAdmin,IsCustomer,IsAdminOrSuperuser
from rest_framework.permissions import IsAuthenticated ,AllowAny,IsAdminUser
from rest_framework import status
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.validators import ValidationError
from django.core.mail import send_mail
import uuid
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db.models import Sum


class UserSignup(CreateAPIView):
    ''' 
    Create a new user account.

    This endpoint allows a new user to sign up by providing the necessary information such as email, password, and any other required fields, also a company can register right from this endpoint'''
    
    queryset = CustomUser.objects.all()
    serializer_class=UserSerializer
    

class LoginAPIView (APIView):
    """
    Handle user login.

    This endpoint allows a user to log in by providing their email and password.
    Upon successful login, an access token and a refresh token are returned. """
   
                                          
    serializer_class = UserLoginSerializer
    @swagger_auto_schema(request_body=UserLoginSerializer)
    def post(self, request):
        data = request.data
        user = CustomUser.objects.filter(email = data['email']) .first()
        if user is None:
            return Response({"message":"user does not exist"})
        if not user.check_password (data['password']):
            return Response({"Message": 'Password Is Incorrect'})
        
        token = RefreshToken.for_user(user)
        return Response({"success": True, "message": "login successfully", 
                         "access_token": str(token.access_token),"refresh_token": str(token) })


    
class UserUpdate(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a user instance.

    get:
    Retrieve own user details.

        Retrieves a user instance by ID. Only the `owner`(ownself) can access the details of the user.
        
    put:
    Fully update own user details.

        Updates a user instance with the provided data. Requires full data replacement.
        Only the `owner`(ownself) can update the user information.

    patch:
    Partially update own details.

        Partially updates a user instance with the provided data. Allows updating specific fields only.
        Only the `owner`(ownself) can make partial updates to the user information.

    delete:
    Delete own profile.

        Deletes a user instance by ID. Only the `owner`(ownself) can delete the user.
    """
    
    queryset = CustomUser.objects.all()
    serializer_class=UserSerializer
    permission_classes = [IsAuthenticated & (IsOwner )]
    

class ProductViewSet(viewsets.ModelViewSet):
    ''' 
    list:
    Retrieve all products.

        Returns the list of products that the current action requires.
        An admin or a staff can view the products of their company whereas the customer can view all the products.
        Even if the user is unauthenticated he/she can view the products but to buy he/she has to be authenticated.
        It allows filtering products by category and company


    create:
    Add a new product.

            Handles the creation of a product, ensuring the user has the necessary 
            permissions and is associated with a company if required. `Admin` and `staff` access only.

    retrieve:
    Get details of a specific product.

        Retrieves a specific product by ID.Only of their own company. `Admin` and `staff` access only.
        
    update:
    Fully update an existing product.

        Updates a specific product.Only of their own company. `Admin` and `staff` access only.
        
    partial_update:
    Partially update an existing product.

        Partially updates a specific product.Only of their own company.`Admin` and `staff` access only.
        
    destroy:
    Delete a specific product.

        Deletes a specific product. Only of their own company. `Admin` and `staff` access only.  
    
    '''
    serializer_class = ProductSerializer
    # filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'company']
    def get_permissions(self):
        

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSuperuser()]  # Permissions for admin or staff only
        return [AllowAny()]  # Allow all users to view products

    
    def get_queryset(self):
        
        user = self.request.user
        if user.is_authenticated:
            if user.company_user:
                return Product.objects.filter(company=user.company_user)
             
        return Product.objects.all()

    def perform_create(self, serializer):
        
        user = self.request.user
        if user.is_authenticated:
            if user.role in ['staff', 'admin']:
                if not user.company_user:
                    raise PermissionDenied("User is not associated with any company.")
                serializer.save(company=user.company_user, Created_by=user)
            else:
                serializer.save(Created_by=user)
        else:
            raise PermissionDenied("User must be authenticated to create a product.")

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_authenticated:
            if user.role in ['staff', 'admin']:
                if not user.company_user:
                    raise PermissionDenied("User is not associated with any company.")
                product = serializer.instance
                if product.company != user.company_user:
                    raise PermissionDenied("You do not have permission to update this product.")
                serializer.save()
            else:
                serializer.save()
        else:
            raise PermissionDenied("User must be authenticated to update a product.")


class CustomerOrderProductView(ListCreateAPIView):

    """
    get:
    Get ordered products of a customer.

        Retrieves a list of orders placed by the currently authenticated customer.
        The view filters orders to include only those associated with the current user.

    post:
    Place an order of a customer.

        Allows the authenticated customer to create a new order.
        The user is automatically associated with the order upon creation.
    """

    queryset = Order.objects.all()  
    serializer_class = UserOrderSerializer
    permission_classes = [ IsAuthenticated ] 

    def get_queryset(self):              
        return Order.objects.filter(user=self.request.user)
    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class AdminOrderView(viewsets.ModelViewSet):
    ''' 
    list:
    Get order list for admin.

        Retrieves a list of all orders associated with the company. `Admins` and `staff` can view all orders.

    create:
    Creates an order.

        Creates a new order. `Admins` and `staff` can create orders. The user creating the order is associated with it.

    retrieve:
    Retrieve a specific order by ID.

        Retrieves details of a specific order by ID of own company. `Admins` and `staff` can view details of any order.

    update:
    Update an existing order.

        Updates an existing order of own company. `Admins` and `staff` can update orders. Requires full data replacement.

    partial_update:
    Partially update an existing order.

        Partially updates an existing order of own company. `Admins` and `staff` can update specific fields of an order.

    destroy:
    Delete a specific order by ID.

        Deletes a specific order by ID of own company. `Admins` and `staff` can delete orders.
        
    
    '''
    # queryset=Order.objects.all()   
    serializer_class = AdminOrderSerializer
    permission_classes=[IsAdminOrSuperuser]

    def get_queryset(self):
        user = self.request.user
        # Get orders with items belonging to the admin's company
        return Order.objects.filter(order_items__product__company=user.company).distinct()

    def get_serializer_context(self):
        return {'request': self.request}

    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

      

class CartItemViewSet(viewsets.ModelViewSet):
    """
    list:
    Retrieve cart items for the authenticated user.

        Retrieves a list of all cart items for the authenticated user. Each user can only view items in their own cart.

    create:
    Add a new item to the cart.

        Adds a new item to the cart for the authenticated user. If the cart does not exist, it will be created.

    retrieve:
    Retrieve details of a specific cart item.

        Retrieves details of a specific cart item by ID for the authenticated user. Only items in the user's cart can be accessed.

    update:
    Fully update a specific cart item.

        Updates an existing cart item. Authenticated users can update their own cart items. Requires full data replacement.

    partial_update:
    Partially update a specific cart item.

        Partially updates an existing cart item. Authenticated users can update specific fields of their own cart items.

    destroy:
    Remove a specific cart item from own's cart.

        Deletes a specific cart item by ID for the authenticated user. Only items in the user's cart can be deleted.
    """
    permission_classes = [IsAuthenticated]
    serializer_class=CartItemSerializer

    def get_queryset(self):
        cart = get_object_or_404(Cart, user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)



class CompanyView(ListCreateAPIView):
    permission_classes = [IsAdminOrSuperuser]
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def perform_create(self, serializer):
        if Company.objects.filter(user=self.request.user).exists():
            raise ValidationError("You already have a company associated with your account.")
        serializer.save(user=self.request.user)



class InviteUserView(CreateAPIView):
    """
    Invite a user via email.

    This view allows an  `admin`  to invite a user to join the platform. The invited user will receive an email with a temporary password and an activation link.
    With that email and the temporary passport the user can login and work as a staff in the designated company.
    """
    permission_classes = [IsAdmin]
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        
        password = get_random_string(length=12)
        hashed_password = make_password(password)
        
        # Retrieve the company_id of the admin who is sending the invitation
        admin_company = self.request.user.company_user
        company_id = admin_company.id if admin_company else None
        
        # Check if the user already exists
        user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'role': role,
            'is_active': False,  # User is inactive by default
            'password': hashed_password,
            'company_user': admin_company  # Correct field assignment
        }
    )

        # Generate a token and store the email and company_id in the cache
        token = str(uuid.uuid4())
        cache.set(f'invite_token_{token}', {'email': email, 'company_id': company_id}, timeout=600)

        # Send the invitation email
        send_invitation_email(user, token, self.request.user.email, password)
        
        if created:
            return Response({'message': 'User created and invitation sent.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Invitation sent to existing user.'}, status=status.HTTP_200_OK)

def send_invitation_email(user, token, from_email, password):
    activation_link = f"http://127.0.0.1:8000/invite/accept/{token}"
    
    subject = 'You are invited!'
    message = f'''
    Please click the following link to activate your account:
    {activation_link}
    Your temporary password is: {password}
    '''
    
    send_mail(
        subject,
        message,
        from_email,
        [user.email],
        fail_silently=False,
    )





def accept_invitation(request, token): 
    if not token:
        return HttpResponse("Invalid invitation link", status=400)
    
    # Retrieve the email and company_id associated with the token
    data = cache.get(f'invite_token_{token}')
    
    if not data:
        return HttpResponse("Invalid invitation link or token has expired", status=400)
    
    email = data['email']
    company_id = data['company_id']
    
    try:
        user = CustomUser.objects.get(email=email)
        if user.is_active:
            return HttpResponse("User is already active", status=400)

        # Activate the user and assign the company
        user.is_active = True
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                user.company_user = company
            except Company.DoesNotExist:
                return HttpResponse("Invalid company", status=400)
        user.save()

        # Remove the token from cache to prevent reuse
        cache.delete(f'invite_token_{token}')

        return HttpResponse("You are activated and eligible to join!", status=200)
    except CustomUser.DoesNotExist:
        return HttpResponse("User not found", status=400)
    


class OrderCompanyStatusUpdateView(APIView): 
    """
    Update status of a product.

    This view allows an  `admin` or `staff` to update the status of a product through choices given. 
    """
    permission_classes=[IsAdmin]
    serializer_class = OrderCompanyStatusSerializer
    def put(self, request, order_id, company_id):
        try:
            order_status = OrderCompanyStatus.objects.get(order_id=order_id, company_id=company_id)
        except OrderCompanyStatus.DoesNotExist:
            return Response({'detail': 'OrderCompanyStatus not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        self.check_object_permissions(request, order_status)

        serializer = OrderCompanyStatusSerializer(order_status, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


