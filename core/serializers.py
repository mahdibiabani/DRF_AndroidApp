from django.core.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer

from rest_framework import serializers

from core.models import CustomUser




class UserCreateSerializer(DjoserUserCreateSerializer):
    confirm_password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    class Meta(DjoserUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password', 'confirm_password']



    def create(self, validated_data):
       confirm_password = validated_data.pop('confirm_password', None)
       if validated_data['password'] != confirm_password:
           raise serializers.ValidationError("Passwords do not match")
       return CustomUser.objects.create_user(**validated_data)

    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         raise ValidationError('passwords dont match')
    #     return data    


    def validate(self, data):
        if  len(data['password']) < 8:
            raise serializers.ValidationError('password should be at least 8 characters')
        return data    

    
# class NumberValidator(object):
#     def validate(self, password, user=None):
#         if not re.findall('\d', password):
#             raise ValidationError(
#                 _("The password must contain at least 1 digit, 0-9."),
#                 code='password_no_number',
#             )

#     def get_help_text(self):
#         return _(
#             "Your password must contain at least 1 digit, 0-9."
#         )


# class UppercaseValidator(object):
#     def validate(self, password, user=None):
#         if not re.findall('[A-Z]', password):
#             raise ValidationError(
#                 _("The password must contain at least 1 uppercase letter, A-Z."),
#                 code='password_no_upper',
#             )

#     def get_help_text(self):
#         return _(
#             "Your password must contain at least 1 uppercase letter, A-Z."
#         )


# class LowercaseValidator(object):
#     def validate(self, password, user=None):
#         if not re.findall('[a-z]', password):
#             raise ValidationError(
#                 _("The password must contain at least 1 lowercase letter, a-z."),
#                 code='password_no_lower',
#             )

#     def get_help_text(self):
#         return _(
#             "Your password must contain at least 1 lowercase letter, a-z."
#         )


# class SymbolValidator(object):
#     def validate(self, password, user=None):
#         if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password):
#             raise ValidationError(
#                 _("The password must contain at least 1 symbol: " +
#                   "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),
#                 code='password_no_symbol',
#             )

#     def get_help_text(self):
#         return _(
#             "Your password must contain at least 1 symbol: " +
#             "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"
#         )




class UserSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        fields = ['id','username']




       