from django import forms
from django.contrib import admin
from .models import Bill, Order, Profile


class OrderForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Profile.objects.all(), required=True)

    class Meta:
        model = Order
        fields = ['customer', 'item', 'invoice_id']


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['table', 'customer', 'dishes']

    # Nếu có tham số `table` trong URL, gán giá trị đó vào field `table`
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kiểm tra nếu có 'table' trong request
        if 'table' in kwargs.get('initial', {}):
            self.fields['table'].initial = kwargs.get('initial').get('table')
