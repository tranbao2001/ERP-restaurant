from django.contrib import admin
from .models import *
from django.utils.html import format_html
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from .models import PurchaseOrder
from django.urls import path

class IngredientAdmin (admin.ModelAdmin):
    list_display = ('code', 'name', 'unit', 'price', 'quantity', 'added_on')  # Các trường sẽ hiển thị trong danh sách
    search_fields = ('code', 'name')
    list_filter = ('unit', 'added_on')  # Bộ lọc theo đơn vị và ngày thêm
    ordering = ('code',)  # Sắp xếp theo mã nguyên liệu

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name','phone_number', 'email', 'address', 'added_on')  # Hiển thị các trường mong muốn
    search_fields = ('name', 'contact_number', 'email')  # Tìm kiếm theo tên, số liên lạc và email
    list_filter = ('added_on',)  # Bộ lọc theo ngày thêm nhà cung ứng
    ordering = ('name',)  # Sắp xếp theo tên nhà cung ứng


    
class StockOutAdmin(admin.ModelAdmin):
    list_display = ['id', 'ingredient', 'quantity', 'unit', 'date_out']  # Hiển thị các trường mong muốn
    list_filter = ['date_out', 'ingredient']  # Bộ lọc theo ngày xuất và nguyên liệu
    search_fields = ['ingredient__name', 'unit']  # Tìm kiếm theo tên nguyên liệu và đơn vị

from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderDetail

class PurchaseOrderDetailInline(admin.TabularInline):
    model = PurchaseOrderDetail
    extra = 1  # Số dòng mẫu khi tạo chi tiết phiếu
    fields = ['ingredient', 'quantity', 'unit_price', 'total_price']  # Các trường cần hiển thị trong inline

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'total_amount', 'created_at', 'is_received']  # Các trường cần hiển thị trong danh sách
    list_filter = ['is_received', 'created_at']  # Lọc theo trạng thái và thời gian
    search_fields = ['order_number', 'supplier__name']  # Tìm kiếm theo mã đơn hàng và tên nhà cung cấp
    inlines = [PurchaseOrderDetailInline]  # Hiển thị chi tiết phiếu nhập hàng
    actions = ['mark_as_received']  # Hành động khi chọn phiếu nhập hàng

    def mark_as_received(self, request, queryset):
        # Thực hiện đánh dấu phiếu nhập hàng là đã nhận
        queryset.update(is_received=True)
        self.message_user(request, "Đã đánh dấu phiếu nhập hàng là đã nhận.")
    mark_as_received.short_description = "Đánh dấu là đã nhận"



class PurchaseOrderDetailAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'ingredient', 'quantity', 'unit_price', 'total_price']  # Các trường cần hiển thị trong chi tiết
  
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:purchase_order_id>/', self.admin_site.admin_view(self.purchase_order_detail_view), name='purchase_order_detail'),
        ]
        return custom_urls + urls

    def purchase_order_detail_view(self, request, purchase_order_id):
        # Lấy đối tượng PurchaseOrder từ ID
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
        
        # Trả về template với đối tượng PurchaseOrder
        return render(request, 'admin/inventory/purchase_order_detail.html', {'purchase_order': purchase_order})


admin.site.register(StockOut, StockOutAdmin)

admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderDetail, PurchaseOrderDetailAdmin)
