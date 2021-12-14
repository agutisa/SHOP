from django import forms


PAYMENT_CHOICES = (
('M', 'Mobile Money'),
('c', 'Cash on Delivery'),
)

class CheckoutForm(forms.Form):
    firstname = forms.CharField(widget=forms.TextInput(attrs={
         'placeholder': 'first name'
         }))
    lastname = forms.CharField(widget=forms.TextInput(attrs={
         'placeholder': 'Last name'
         }))
    mobilenumber = forms.CharField(widget=forms.TextInput(attrs={
         'placeholder': 'Mobile number'
          }))
    address = forms.CharField(widget=forms.TextInput(attrs={
         'placeholder': 'address'
         }))
    town = forms.CharField(widget=forms.TextInput(attrs={
         'placeholder': 'Town'
          }))
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
    widget=forms.RadioSelect, choices=PAYMENT_CHOICES)

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
         'class': 'form-control',
         'placeholder': 'Promo code',
         'aria-label':'Recipient\'s username',
          'aria-describedby':'basic-addon2'
          }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
         'rows': 4
          }))
    email = forms.EmailField()
