from django import forms
from .models import PurchaseOrder, PurchaseOrderDetail

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['order_code', 'order_date']

class PurchaseOrderDetailForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderDetail
        fields = ['ingredient', 'quantity', ]

    