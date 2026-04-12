from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import authenticate,get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.serializers import Serializer, ModelSerializer,ValidationError,CharField,UUIDField,ChoiceField ,SerializerMethodField ,EmailField
import re


from .models import (
    UserRole,CustomerProfile,CustomerAddress,
    RestaurantOwnerProfile,DeliveryAgentProfile,
    EmailVerificationToken
)

User = get_user_model()

#for creating tokens 
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] =user.role
    refresh['name'] = user.name
    return {
        'refresh' : str(refresh),
        'access' :str(refresh.access_token)
    }



#Registration 

class CustomerRegistrationSerializer(ModelSerializer):
    password = CharField(write_only=True,min_length=8)
    tokens = SerializerMethodField(read_only=True)

    class Meta: 
        model = User
        fields = ('id','email','phone','name','password','tokens')
        read_only_fields= ('id','tokens')

    def validate_email(self, value):
        EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(EMAIL_PATTERN, value):
            raise ValidationError({"email": "Invalid email format."})
        return value
        
    def create(self,validated_data):
        user = User.objects.create_user(
            role=UserRole.CUSTOMER,**validated_data
        )
        CustomerProfile.objects.create(user=user)
        return user
        
    def get_tokens(self,user):
        return get_tokens_for_user(user)


class RestaurantOwnerRegistrationSerializer(ModelSerializer):
    password = CharField(write_only=True,min_length=8)
    tokens = SerializerMethodField(read_only=True)

    class Meta : 
        model = User
        fields = ('id','email','phone','name','password','tokens')
        read_only_fields= ('id','tokens')

    def validate_email(self, value):
        EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(EMAIL_PATTERN, value):
            raise ValidationError({"email": "Invalid email format."})
        return value
    
    def create(self,validated_data):
        user = User.objects.create_user(
            role=UserRole.RESTAURANT_OWNER,**validated_data
        )
        RestaurantOwnerProfile.objects.create(user=user)
        return user
        
    def get_tokens(self,user):
        return get_tokens_for_user(user)
    

class DeliveryAgentRegistrationSerializer(ModelSerializer):
    password = CharField(write_only=True,min_length=8)
    tokens = SerializerMethodField(read_only=True)
    vehicle_type = ChoiceField(choices=DeliveryAgentProfile.VehicleType.choices)
    vehicle_number = CharField(max_length=15)
    driving_license = CharField(max_length=20)

    class Meta : 
        model = User
        fields = ('id','email','phone','name','password',
                  'vehicle_type','vehicle_number','driving_license','tokens')
        read_only_fields= ('id','tokens')

    def validate_email(self, value):
        EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(EMAIL_PATTERN, value):
            raise ValidationError({"email": "Invalid email format."})
        return value
    
    def create(self,validated_data):
        vehicle_type=validated_data.pop('vehicle_type')
        vehicle_number=validated_data.pop('vehicle_number')
        driving_license=validated_data.pop('driving_license')

        user = User.objects.create_user(
            role=UserRole.DELIVERY_AGENT,**validated_data
        )
        DeliveryAgentProfile.objects.create(user=user,
        vehicle_type=vehicle_type,
        vehicle_number=vehicle_number,
        driving_license=driving_license
        )
        return user
        
    def get_tokens(self,user):
        return get_tokens_for_user(user)
    

#Login flow 
class LoginSerializer(serializers.Serializer):
    email = EmailField()
    password = CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            
            if not user.is_active:
                raise serializers.ValidationError('This account has been deactivated')
        else:
            raise serializers.ValidationError('Must include "email" and "password".')

        attrs['user'] = user
        return attrs


class TokenResponseSerializer(Serializer):
        '''Response structure after successful login/register flow'''
        access = CharField()
        refresh = CharField()
        role=CharField(source='user.role')
        name=CharField(source='user.name')
        user_id =UUIDField(source='user.id')


class ChangePasswordSerializer(Serializer):
    old_password = CharField(write_only=True)
    new_password = CharField(write_only=True,min_length=8)

    def validate_old_password(self,value):
        if not self.context['request'].user.check_password(value):
            raise ValidationError('Old password is incorrect')
        return value



class ForgotPasswordSerializer(Serializer):
    email = EmailField()
    def validate_email(self,value):
        try:
            user = User.objects.get(email=value,is_active=True)
        except User.DoesNotExist:
            return value
        self.context['user']=user
        return value

class ResetPasswordSerializer(Serializer):
    new_password = CharField(write_only=True,min_length=8)
    confirm_password=CharField(write_only=True)
    
    def validate(self,attrs):
        token = self.context['token']
        #verify token
        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(token=token)
        except EmailVerificationToken.DoesNotExist:
            raise ValidationError({'error':'Invalid Password Reset Link'})
        
        if not token_obj.is_valid():
            raise ValidationError({'error':'Token is Invalid or Expired'})
        
        if attrs.get('new_password')!=attrs.get('confirm_password'):
            raise ValidationError({'password_mismatch':'Passwords do not match'})
        
        self.context['token_obj']=token_obj
        return attrs





#Customer Profile & Address 
class CustomerAddressSerializer(ModelSerializer):
    class Meta : 
        model = CustomerAddress
        fields = ('id','label','formatted_address','address_line',
                  'pincode','flat_number','receiver_phone','lat','long','is_default',)
        read_only_fields=('id',)



class CustomerProfileSerializer(ModelSerializer):
    email = EmailField(source='user.email',read_only=True)
    phone = CharField(source='user.phone',read_only=True)
    name = CharField(source='user.name')
    addresses = CustomerAddressSerializer(many=True,read_only=True)

    class Meta : 
        model = CustomerProfile
        fields = ('email','phone','name','avatar','date_of_birth',
                  'is_vegetarian','total_orders','loyalty_points',
                  'addresses')

    read_only_fields = ('total_orders','loyalty_points')

    def update(self,instance,validated_data):
        #handles nested user fields 
        user_data=validated_data.pop('user',{})
        if 'name' in user_data:
            instance.user.name=user_data.get('name')
            instance.use.save(update_fields=['name'])
        return super().update(instance,validated_data)
        


class RestaurantOwnerProfileSerializer(ModelSerializer):
    email = EmailField(source='user.email',read_only=True)
    phone = CharField(source='user.phone',read_only=True)
    name = CharField(source='user.name')

    class Meta:
        model = RestaurantOwnerProfile
        fields = ('email','phone','name','pan_number','gst_number','is_verified')
        read_only_fields=('is_verified',)


    def update(self,instance,validated_data):
        user_data = validated_data.pop('user',{})
        if 'name' in user_data:
            instance.user.name=user_data.get('name')
            instance.user.save(update_fields=['name'])
            return super().update(instance,validated_data)
        

class DeliveryAgentProfileSerializer(ModelSerializer):
    email = EmailField(source='user.email',read_only=True)
    phone = CharField(source='user.phone',read_only=True)
    name = CharField(source='user.name')

    class Meta:
        model=DeliveryAgentProfile
        fields = ('email','phone','name','avatar','vehicle_number',
                  'vehicle_type','driving_license','status','lat',
                  'long','last_location_update','total_deliveries',
                  'average_rating','is_verified')
        read_only_fields =('last_location_update','lat','long'
                           ,'total_deliveries','average_rating',
                           'is_verified')
        
    def update(self,instance,validated_data):
        user_data = validated_data.pop('user',{})
        if 'name' in user_data:
            instance.user.name=user_data.get('name')
            instance.user.save(update_fields=['name'])
            return super().update(instance,validated_data)
  


class AgentLocationUpdateSerializer(Serializer):
     lat = serializers.DecimalField(max_digits=9,decimal_places=6)
     long = serializers.DecimalField(max_digits=9,decimal_places=6)
     status=ChoiceField(choices=DeliveryAgentProfile.AgentStatus.choices,required=False)



    
   






#Email Verification 

class EmailVerificationSerializer(Serializer):
    token = UUIDField()

    def validate_token(self,value):
        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise ValidationError('Invalid verification link')
        
        if not token_obj.is_valid():
            raise ValidationError('Verification link is expired,request a new one')
        
        if token_obj.user.is_email_verified:
            raise ValidationError('This email is Already Verified')
        
        self.context['token_obj'] = token_obj
        return value
    

class ResendVerificationEmailSerializer(Serializer):
    email  = EmailField()

    def validate_email(self,value):
        try:
            user = User.objects.get(email=value,is_active=True)
        except User.DoesNotExist:
            return value
        
        if user.is_email_verified: #type:ignore
            raise ValidationError('This email is already verified')

        self.context['user'] = user
        return value

