from traceback import format_tb
from django.utils.html import format_html
from django.contrib import admin
from myapp.models import Bill, BillDish, Contact, Category, Table, Team, Dish, Profile, Order
from django.http import HttpResponseRedirect
from .forms import BillForm
from django.urls import path
from django.shortcuts import render, get_object_or_404

admin.site.site_header = "FiveFood | admin"


def view_dishes_in_table(modeladmin, request, queryset):
    for table in queryset:
        if table.is_occupied and table.current_bill:
            # Chuyển hướng đến hóa đơn chi tiết của bàn
            return HttpResponseRedirect(f"/admin/myapp/bill/{table.current_bill.id}/change/")
        else:
            modeladmin.message_user(
                request, f"Bàn {table.name} hiện không có khách.")


view_dishes_in_table.short_description = "Xem món trong bàn"


class TableAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_occupied', 'current_bill_display']
    actions = ['create_order_for_table']

    def current_bill_display(self, obj):
        # Lấy hóa đơn chưa thanh toán mới nhất
        current_bill = obj.get_current_unpaid_bill()
        if current_bill:
            # Tạo liên kết tới trang chi tiết của Bill
            return format_html(
                '<a href="/admin/myapp/bill/{}/">Bill #{}</a> - {}',
                current_bill.id,  # Đường dẫn tới trang chi tiết Bill
                current_bill.id,
                current_bill.time.strftime('%Y-%m-%d %H:%M:%S')
            )
        else:
            # Nếu không có hóa đơn chưa thanh toán, tạo liên kết để tạo mới Bill
            return format_html(
                '<a href="{}">Tạo Bill mới</a>',
                # Đường dẫn tới trang tạo Bill mới
                f'/admin/myapp/bill/add/?table={obj.id}'
            )
        return "Chưa có hóa đơn chưa thanh toán"
    current_bill_display.short_description = "Hóa đơn chưa thanh toán"

    def create_order_for_table(self, request, queryset):
        for table in queryset:
            # Kiểm tra xem bàn có hóa đơn chưa thanh toán hay không
            current_bill = table.get_current_unpaid_bill()

            if not current_bill:
                # Nếu không có hóa đơn chưa thanh toán, tạo một hóa đơn mới
                bill = Bill.objects.create(
                    table=table,
                    total_price=0,  # Có thể thay đổi theo yêu cầu
                    is_payed=False,
                )
                order = Order.objects.create(
                    customer=None,  # Bạn có thể yêu cầu nhập tên khách hàng sau
                    item=None,  # Bạn có thể thêm món ăn nếu cần
                    status=False,
                    invoice_id=f"INV{bill.id}",  # Tạo invoice id từ bill
                )

                # Thêm thông báo
                self.message_user(
                    request, f"Order và Bill đã được tạo cho bàn {table.name}")
            else:
                self.message_user(
                    request, f"Bàn {table.name} đã có hóa đơn chưa thanh toán.")

        return HttpResponseRedirect("/admin/myapp/bill/")

    create_order_for_table.short_description = "Tạo Order cho Bàn (nếu chưa có Bill)"


class ContactAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email',
                    'subject', 'added_on', 'is_approved']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'added_on', 'updated_on']


class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'added_on', 'updated_on']


class DishAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'added_on', 'updated_on']
    # actions = [mark_as_paid_and_redirect]


class BillDishInline(admin.TabularInline):
    model = BillDish
    extra = 1


class BillAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'customer',
                    'total_price', 'is_payed', 'time']

    form = BillForm

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:bill_id>/',
                 self.admin_site.admin_view(self.bill_detail_view), name='bill_detail'),
        ]
        return custom_urls + urls

    def bill_detail_view(self, request, bill_id):
        # Lấy Bill từ database theo ID
        bill = get_object_or_404(Bill, id=bill_id)

        # Trả về trang chi tiết Bill trong Admin
        context = {
            **self.admin_site.each_context(request),  # Thêm các thành phần như sidebar, breadcrumbs
            'bill': bill,
            'title': f"Chi tiết Hóa đơn #{bill.id}",
        }
        return render(request, 'admin/myapp/bill_detail.html', context)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Nếu có tham số `table` trong URL, tự động điền vào trường `table` trong form
        if 'table' in request.GET:
            form.base_fields['table'].initial = request.GET['table']
        return form

    inlines = [BillDishInline]
    list_filter = ['is_payed', 'time']
    search_fields = ['table', 'customer__user__username']


admin.site.register(Table, TableAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Dish, DishAdmin)
admin.site.register(Profile)
admin.site.register(Order)
