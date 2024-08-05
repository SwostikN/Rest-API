from django.urls import path,include
from .views import OrderCompanyStatusUpdateView,ProductViewSet,accept_invitation,InviteUserView,CompanyView,UserSignup,LoginAPIView,UserUpdate,CustomerOrderProductView,AdminOrderView,CartItemViewSet

from rest_framework.routers import DefaultRouter

orders_router = DefaultRouter()
orders_router.register(r'orders', AdminOrderView, basename='admin-orders')

cart_router = DefaultRouter()
cart_router.register(r'cart', CartItemViewSet, basename='cart')

product_router = DefaultRouter()
product_router.register(r'product', ProductViewSet, basename='product')


urlpatterns = [
    path('', include(orders_router.urls)),
    path('', include(cart_router.urls)),
    path('', include(product_router.urls)),
    # path('', include(company_router.urls)),
    path('signup/',UserSignup.as_view() , name='add-signup'),
    path('login/',LoginAPIView.as_view() , name='add-login'),
    path('user/<int:pk>/', UserUpdate.as_view(), name='user-update'),
    # path('products/', ProductView.as_view(), name='product-list-create'),
    # path('company/', CompanyView.as_view(), name='company'),
    path('invite/', InviteUserView.as_view(), name='invite'),
    path('order/', CustomerOrderProductView.as_view(), name='order'),
    path('invite/accept/<str:token>/', accept_invitation, name='accept_invitation'),
    path('update-status/<int:order_id>/<int:company_id>/', OrderCompanyStatusUpdateView.as_view(), name='order-company-status-update'),

           
]

# tabaxib497@mfunza.com
# cuNzdTgVaB92