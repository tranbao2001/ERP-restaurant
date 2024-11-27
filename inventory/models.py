from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F
class Ingredient(models.Model):
    code = models.CharField(max_length=50, unique=True)  # Mã nguyên liệu, có độ dài tối đa 50 ký tự và phải duy nhất
    name = models.CharField(max_length=200)  # Tên nguyên liệu
    unit = models.CharField(max_length=50)  # Đơn vị (kg, lít, cái, ...)
    price = models.FloatField()  # Giá tiền của nguyên liệu (float để hỗ trợ giá có số thập phân)
    quantity = models.IntegerField(default=0)  # Số lượng nguyên liệu hiện tại trong kho
    added_on = models.DateTimeField(auto_now_add=True)  # Ngày thêm nguyên liệu vào kho (Tự động điền khi tạo mới)

    def __str__(self):
        return f"{self.code} - {self.name}"  # Hiển thị mã nguyên liệu và tên nguyên liệu khi gọi object

    class Meta:
        verbose_name_plural = "Ingredients"  # Đặt tên dạng số nhiều cho bảng trong admin
    
    # Model Nhà Cung Cấp
class Supplier(models.Model):
    name = models.CharField(max_length=200)  # Tên nhà cung cấp
    contact_person = models.CharField(max_length=100, blank=True, null=True)  # Người liên hệ (tùy chọn)
    address = models.TextField(blank=True, null=True)  # Địa chỉ
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Số điện thoại
    email = models.EmailField(blank=True, null=True)  # Email của nhà cung cấp
    added_on = models.DateTimeField(auto_now_add=True)  # Ngày tạo nhà cung cấp (tự động điền khi tạo mới)
    updated_on = models.DateTimeField(auto_now=True)  # Ngày cập nhật thông tin nhà cung cấp

    def __str__(self):
        return self.name  # Hiển thị tên nhà cung cấp khi gọi object

    class Meta:
        verbose_name_plural = "Suppliers"  # Đặt tên dạng số nhiều cho bảng trong admin
    
   

class StockOut(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="stock_outs")
    quantity = models.IntegerField()  # Số lượng xuất
    unit = models.CharField(max_length=50)  # Đơn vị
    date_out = models.DateTimeField(auto_now_add=True)  # Ngày xuất (tự động lấy từ thời gian thực)

    def save(self, *args, **kwargs):
        # Kiểm tra số lượng trước khi xuất kho
        if self.ingredient.quantity < self.quantity:
            raise ValidationError(f"Không đủ {self.ingredient.name} trong kho để xuất {self.quantity} {self.unit}!")
        # Cập nhật số lượng trong kho nguyên liệu
        self.ingredient.quantity = F('quantity') - self.quantity
        self.ingredient.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Phiếu xuất: {self.ingredient.name} - {self.quantity} {self.unit}"

    class Meta:
        verbose_name_plural = "Stock Out Records"


from django.db import models
from django.contrib.auth import get_user_model


class PurchaseOrder(models.Model):
    order_number = models.CharField(max_length=100,default='DEFAULT_ORDER')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, null= True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_received = models.BooleanField(default=False)

    def __str__(self):
        return self.order_number

class PurchaseOrderDetail(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null= True)
    def __str__(self):
        return f'{self.ingredient} - {self.quantity}'

    def save(self, *args, **kwargs):
        # Tính lại thành tiền mỗi khi lưu
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)