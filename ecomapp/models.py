from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff','Staff'),
        ('customer', 'Customer'),
        
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    email = models.EmailField(unique=True)
    username=models.CharField(max_length=1000,unique=False, blank=True, null=True)
    company_user = models.ForeignKey('Company', on_delete=models.SET_NULL, related_name='company_users', null=True, blank=True)
    
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []    

        
class Company(models.Model):
    name = models.CharField(max_length=255,unique=False, blank=True, null=True)
    owner=models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name='company' )


    def __str__(self):
        return self.name
   
class Category(models.Model):
    name=models.CharField(max_length=1000,unique=False, blank=True, null=True)
    def __str__(self):
        return self.name
    
    
    
class Product(models.Model):
    Product_name = models.CharField(max_length=100)
    Quantity = models.PositiveIntegerField()
    price = models.FloatField()
    discount=models.FloatField(default=0)
    Description=models.TextField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products', null=True)
    category=models.ForeignKey(Category, on_delete=models.CASCADE)
    Created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_products')

    def get_discounted_price(self):
        if self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to="products")




class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ordered_products = models.ManyToManyField(Product, through='OrderItem')
    date_ordered = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255)
    time_of_delivery = models.TimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    companies = models.ManyToManyField(Company, through='OrderCompanyStatus')
    

    def calculate_total_price(self):
        self.total_price = sum(item.amount for item in self.order_items.all())
        self.save()

    

class OrderItem(models.Model): 
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        
        self.amount = self.quantity * self.product.get_discounted_price()
        super(OrderItem, self).save(*args, **kwargs)


class OrderCompanyStatus(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('order', 'company')  # Ensures one status per company per order

    def __str__(self):
        return f"Order {self.order.id} - Company {self.company.name} - Status {self.status}"



class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} for {self.user.first_name}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.cart_items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='cart_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.product.get_discounted_price()
        super(CartItem, self).save(*args, **kwargs)

    def get_total_price(self):
        return self.total_price
    






    