from django.contrib.auth.models import AbstractBaseUser ,PermissionsMixin,BaseUserManager
from django.utils.translation import gettext_lazy as _ 
from django.core.validators import RegexValidator
from django.utils import timezone
from django.db import models
from decimal import Decimal
import uuid 


#user role choices for different profiles 
class UserRole(models.TextChoices):
    CUSTOMER='CUSTOMER',     'Customer'
    RESTAURANT_OWNER = 'RESTAURANT_OWNER', 'Restaurant Owner'
    DELIVERY_AGENT = 'DELIVERY_AGENT'  , 'Delivery Agent'


#extending default baseusermanager to add new functionality 
class UserManager(BaseUserManager):
     def create_user(self,email,password=None,**extras):
        if not email:
            raise ValueError('email is required')
        email = self.normalize_email(email)  
        user = self.model(email=email,**extras)
        user.set_password(password)        
        user.save(using=self._db)
        return user
     
     def create_superuser(self,email,password=None,**extras):
          extras.setdefault('is_staff',True)
          extras.setdefault('is_superuser',True)
          return self.create_user(email,password,**extras)

        


#extending django default BaseUser for adding new properties and change the username identity for authentication to email
class User(AbstractBaseUser,PermissionsMixin):
        id = models.UUIDField(_("userId"), primary_key=True,default=uuid.uuid4,editable=False)
        email = models.EmailField(_("email address"), unique=True)
        name = models.CharField(_("full name"), max_length=100)
        phone= models.CharField(_("phone number"), max_length=15, unique=True,null=True,blank=True)
        role = models.CharField(_("user role"), max_length=20, choices=UserRole.choices,default=UserRole.CUSTOMER)

        #flags 
        is_active= models.BooleanField(_("Active Status"), default=True)
        is_staff = models.BooleanField(_("Staff Status"), default=False)
        is_phone_verified = models.BooleanField(_("Phone Verified"), default=False)
        is_email_verified = models.BooleanField(_("Email Verified"), default=False)

        date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

        objects=UserManager()

        USERNAME_FIELD = 'email'
        REQUIRED_FIELDS = ['name']
        
        class Meta: 
              db_table = 'users'
              verbose_name = 'User'
              verbose_name_plural = 'Users'

        def __str__(self):
            return f"{self.email} ({self.role})"


        @property
        def is_customer(self):
            return self.role == UserRole.CUSTOMER
        
        @property
        def is_restaurant_owner(self):
            return self.role == UserRole.RESTAURANT_OWNER
        
        @property
        def is_delivery_agent(self):
             return self.role == UserRole.DELIVERY_AGENT



class CustomerProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='customer_profile')
    avatar = models.ImageField(_('Profile Picture'),upload_to='avatar/customers/',null=True,blank=True)
    date_of_birth = models.DateField(_('Date of Birth'),null=True,blank=True) 
    is_vegetarian = models.BooleanField(_("Vegetarian"),default=False)
    total_orders = models.PositiveIntegerField(_("Total Orders"),default=0)
    loyalty_points = models.PositiveIntegerField(_("Loyalty Points"),default=0)
    updated_at = models.DateTimeField(_("Update At"), auto_now=True)

    def __str__(self):
         return self.user.email 
    




class CustomerAddress(models.Model):
    class AddressType(models.TextChoices):
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        CustomerProfile, 
        on_delete=models.CASCADE, 
        related_name='addresses'
    )
    
    # 1. The " Maps api" Data (Crucial for Geofencing)
    formatted_address = models.TextField(_("Map Formatted Address"),blank=True)
    
    # 2. Precise Coordinates (Used for distance-based delivery fees)
    lat = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6,null=True,blank=True)
    long = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6,null=True,blank=True)

    label = models.CharField(_("Address Type"), max_length=10, choices=AddressType.choices, default=AddressType.HOME)
    flat_number = models.CharField(_("House/Flat/Floor No."), max_length=100)
    address_line = models.CharField(_("Apartment/Road/Area"), max_length=250)
    landmark = models.CharField(_("Landmark"), max_length=250,blank=True)
    pincode = models.CharField(
        _("Pin Code"), 
        max_length=6, 
        validators=[RegexValidator(r'^\d{6}$', _("Enter a valid 6-digit pincode"))]
    )
    receiver_phone = models.CharField(
        _("Receiver Phone"), 
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', _("Enter a valid phone number"))]
    ) 
    is_default = models.BooleanField(_("Is Default"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = _("Customer Address")
        verbose_name_plural = _("Customer Addresses")

    def save(self, *args, **kwargs):
        if self.is_default:
            # Atomic update ensures only one default exists
            CustomerAddress.objects.filter(customer=self.customer, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.user.email} - {self.label} ({self.address_line})"
     



class RestaurantOwnerProfile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='owner_profile')
    avatar = models.ImageField(_("Profile Picture"), upload_to='avatars/owners/',null=True,blank=True)
    pan_number=models.CharField(_("Pan Number"), max_length=50,blank=True)
    gst_number=models.CharField(_("Gst number"), max_length=50,blank=True)
    is_verified= models.BooleanField(_("Verification Status"),default=False)
    updated_at = models.DateTimeField(auto_now=True)
        
    
    def __str__(self):
        return f"Owner Profile-{self.user.email}"


class DeliveryAgentProfile(models.Model):
    class VehicleType(models.TextChoices):
        BICYCLE    = "BICYCLE",    "Bicycle"
        SCOOTER    = "SCOOTER",    "Scooter"
        BIKE = "BIKE", "Bike"
 
    class AgentStatus(models.TextChoices):
        OFFLINE     = "OFFLINE",     "Offline"
        AVAILABLE   = "AVAILABLE",   "Available"
        ON_DELIVERY = "ON_DELIVERY", "On Delivery"
    
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='agent_profile')
    avatar = models.ImageField(_('Agent Profile Picture'),null=True,blank=True)
    #about vehicle
    vehicle_type = models.CharField(_("Vehicle Type"), max_length=10 ,choices=VehicleType.choices,default=VehicleType.BIKE)
    vehicle_number = models.CharField(_("Vehicle Number"), max_length=15)
    driving_license = models.CharField(_("Driving License"), max_length=20)

    #live tracking field -frequently updated 
    status=models.CharField(_("Agent Status"), max_length=15,choices=AgentStatus.choices,default=AgentStatus.AVAILABLE)
    lat = models.DecimalField(_("Current Latitude"), max_digits=9, decimal_places=6,null=True,blank=True)
    long = models.DecimalField(_("Current longitude"), max_digits=9, decimal_places=6,null=True,blank=True)
    last_location_update = models.DateTimeField(_("Last Location Update"),null=True,blank=True)

    total_deliveries = models.PositiveIntegerField(_("Total Deliveries"),default=0)
    average_rating = models.DecimalField(_("Average Rating"), max_digits=3, decimal_places=2,default=Decimal(0.00))
    is_verified = models.BooleanField(_("Is Verified"),default=False)
    updated_at = models.DateTimeField(_('Updated At'),auto_now=True)

    def __str__(self):
        return f"Delivery Agent Profile- {self.user.email}:{self.status}"





        
#Email verification model for email verifications 
class EmailVerificationToken(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='email_verification_token')
     token = models.UUIDField(_("Verification Token"),unique=True,default=uuid.uuid4)
     expires_at = models.DateTimeField(_("Expiry Time"))
     created_at  = models.DateTimeField(_('Created At'),auto_now_add=True)

     class Meta:
          db_table= 'email_verification_tokens'

     def is_valid(self):
        # Validate the token 
        return timezone.now() <self.expires_at
     
     def __str__(self):
          return f"verification token for {self.user.email}"




