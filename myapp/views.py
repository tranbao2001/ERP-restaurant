from django.shortcuts import render, get_object_or_404, reverse, redirect
from myapp.models import Contact, Dish, Team, Category, Profile, Order, Table, Bill
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import paypalrestsdk
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import DishSerializer, CategorySerializer, TableSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import json


def index(request):
    context = {}
    cats = Category.objects.all().order_by('name')
    context['categories'] = cats
    # print()
    dishes = []
    for cat in cats:
        dishes.append({
            'cat_id': cat.id,
            'cat_name': cat.name,
            'cat_img': cat.image,
            'items': list(cat.dish_set.all().values())
        })
    context['menu'] = dishes
    return render(request, 'index.html', context)


def contact_us(request):
    context = {}
    if request.method == "POST":
        name = request.POST.get("name")
        em = request.POST.get("email")
        sub = request.POST.get("subject")
        msz = request.POST.get("message")

        obj = Contact(name=name, email=em, subject=sub, message=msz)
        obj.save()
        context['message'] = f"Dear {name}, Thanks for your time!"

    return render(request, 'contact.html', context)


def about(request):
    return render(request, 'about.html')


def team_members(request):
    context = {}
    members = Team.objects.all().order_by('name')
    context['team_members'] = members
    return render(request, 'team.html', context)


def all_dishes(request):
    context = {}
    dishes = Dish.objects.all()
    if "q" in request.GET:
        id = request.GET.get("q")
        dishes = Dish.objects.filter(category__id=id)
        context['dish_category'] = Category.objects.get(id=id).name

    context['dishes'] = dishes
    return render(request, 'all_dishes.html', context)


def register(request):
    context = {}
    if request.method == "POST":
        # fetch data from html form
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('pass')
        contact = request.POST.get('number')
        check = User.objects.filter(username=email)
        if len(check) == 0:
            # Save data to both tables
            usr = User.objects.create_user(email, email, password)
            usr.first_name = name
            usr.save()

            profile = Profile(user=usr, contact_number=contact)
            profile.save()
            context['status'] = f"User {name} Registered Successfully!"
        else:
            context['error'] = f"A User with this email already exists"

    return render(request, 'register.html', context)


def check_user_exists(request):
    email = request.GET.get('usern')
    check = User.objects.filter(username=email)
    if len(check) == 0:
        return JsonResponse({'status': 0, 'message': 'Not Exist'})
    else:
        return JsonResponse({'status': 1, 'message': 'A user with this email already exists!'})


def signin(request):
    context = {}
    if request.method == "POST":
        email = request.POST.get('email')
        passw = request.POST.get('password')

        check_user = authenticate(username=email, password=passw)
        if check_user:
            login(request, check_user)
            if check_user.is_superuser or check_user.is_staff:
                return HttpResponseRedirect('/admin')
            return HttpResponseRedirect('/dashboard')
        else:
            context.update(
                {'message': 'Invalid Login Details!', 'class': 'alert-danger'})

    return render(request, 'login.html', context)


def dashboard(request):
    context = {}
    login_user = get_object_or_404(User, id=request.user.id)
    # fetch login user's details
    profile = Profile.objects.get(user__id=request.user.id)
    context['profile'] = profile

    # update profile
    if "update_profile" in request.POST:
        print("file=", request.FILES)
        name = request.POST.get('name')
        contact = request.POST.get('contact_number')
        add = request.POST.get('address')

        profile.user.first_name = name
        profile.user.save()
        profile.contact_number = contact
        profile.address = add

        if "profile_pic" in request.FILES:
            pic = request.FILES['profile_pic']
            profile.profile_pic = pic
        profile.save()
        context['status'] = 'Profile updated successfully!'

    # Change Password
    if "change_pass" in request.POST:
        c_password = request.POST.get('current_password')
        n_password = request.POST.get('new_password')

        check = login_user.check_password(c_password)
        if check == True:
            login_user.set_password(n_password)
            login_user.save()
            login(request, login_user)
            context['status'] = 'Password Updated Successfully!'
        else:
            context['status'] = 'Current Password Incorrect!'

    # My Orders
    orders = Order.objects.filter(
        customer__user__id=request.user.id).order_by('-id')
    context['orders'] = orders
    return render(request, 'dashboard.html', context)


def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


def single_dish(request, id):
    context = {}
    dish = get_object_or_404(Dish, id=id)

    if request.user.is_authenticated:
        cust = get_object_or_404(Profile, user__id=request.user.id)
        order = Order(customer=cust, item=dish)
        order.save()
        inv = f'INV0000-{order.id}'

        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': dish.discounted_price,
            'item_name': dish.name,
            'user_id': request.user.id,
            'invoice': inv,
            'notify_url': 'http://{}{}'.format(settings.HOST, reverse('paypal-ipn')),
            'return_url': 'http://{}{}'.format(settings.HOST, reverse('payment_done')),
            'cancel_url': 'http://{}{}'.format(settings.HOST, reverse('payment_cancel')),
        }

        order.invoice_id = inv
        order.save()
        request.session['order_id'] = order.id

        form = PayPalPaymentsForm(initial=paypal_dict)
        context.update({'dish': dish, 'form': form})

    return render(request, 'dish.html', context)


def payment_done(request):
    pid = request.GET.get('PayerID')
    order_id = request.session.get('order_id')
    order_obj = Order.objects.get(id=order_id)
    order_obj.status = True
    order_obj.payer_id = pid
    order_obj.save()

    return render(request, 'payment_successfull.html')


def payment_cancel(request):
    # remove comment to delete cancelled order
    # order_id = request.session.get('order_id')
    # Order.objects.get(id=order_id).delete()

    return render(request, 'payment_failed.html')


@login_required
def book_table(request):
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Tạo Profile mới nếu không tồn tại
        user_profile = Profile.objects.create(user=request.user)

    if request.method == "POST":
        table_id = request.POST.get("table_id")
        time = request.POST.get("time")

        try:
            table = Table.objects.get(id=table_id, is_occupied=False)

            # Tạo Bill mới cho bàn
            bill = Bill.objects.create(
                table=table,
                customer=user_profile,
                total_price=0,
                is_payed=False,
                time=time,
            )

            # Cập nhật trạng thái bàn
            table.is_occupied = True
            table.current_bill = bill
            table.save()

            messages.success(request, f"Bạn đã đặt bàn {
                             table.name} thành công!")
        except Table.DoesNotExist:
            messages.error(request, "Bàn không hợp lệ hoặc đã được đặt!")

        return redirect("book_table")

    my_tables = Table.objects.filter(current_bill__customer=user_profile)
    available_tables = Table.objects.filter(is_occupied=False)

    return render(
        request,
        "book_table.html",
        {"my_tables": my_tables, "available_tables": available_tables},
    )


@login_required
def edit_table(request, table_id):
    # Chỉnh sửa hóa đơn/bàn nếu cần
    table = get_object_or_404(
        Table, id=table_id, current_bill__customer__user=request.user)
    if request.method == "POST":
        # Logic cập nhật nếu có form chỉnh sửa
        messages.success(request, f"Đã cập nhật bàn {table.name} thành công!")
        return redirect("book_table")
    return render(request, "edit_table.html", {"table": table})


@login_required
def delete_table(request, table_id):
    table = get_object_or_404(
        Table, id=table_id, current_bill__customer__user=request.user)
    if request.method == "POST":
        # Hủy đặt bàn
        table.is_occupied = False
        if table.current_bill:
            table.current_bill.delete()  # Xoá bill liên quan
        table.current_bill = None
        table.save()
        messages.success(request, f"Đã hủy đặt bàn {table.name}.")
        return redirect("book_table")

# API cho Dish


class DishViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dish.objects.filter(is_available=True)
    serializer_class = DishSerializer

# API cho Category


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

# API cho Table (Danh sách bàn và đặt bàn)


class TableViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        tables = Table.objects.all()
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    def create(self, request):
        data = request.data
        user = request.user.profile  # Lấy thông tin khách hàng từ tài khoản đã đăng nhập
        table_id = data.get('table_id')

        try:
            table = Table.objects.get(id=table_id, is_occupied=False)
            table.is_occupied = True
            table.save()
            return Response({'message': f'Bạn đã đặt bàn {table.name} thành công.'}, status=status.HTTP_201_CREATED)
        except Table.DoesNotExist:
            return Response({'error': 'Bàn không khả dụng hoặc đã được đặt.'}, status=status.HTTP_400_BAD_REQUEST)


def menu(request):
    categories = Category.objects.all()
    menu = [
        {
            "cat_id": category.id,
            "cat_name": category.name,
            "cat_img": category.image.url if category.image else '',
            "items": Dish.objects.filter(category=category, is_available=True).values()
        }
        for category in categories
    ]
    return render(request, 'menu.html', {"menu": menu, "categories": categories})


@csrf_exempt  # Nếu bạn gặp lỗi CSRF
@login_required
def book_table_api(request):
    if request.method == 'POST':
        try:
            # Parse dữ liệu JSON từ request
            data = json.loads(request.body)
            table_id = data.get('table_id')
            time = data.get('time')

            # Kiểm tra bàn
            table = Table.objects.get(id=table_id)

            if table.is_occupied:
                return JsonResponse({"success": False, "message": "Bàn đã được đặt trước đó."}, status=400)

            # Lấy thông tin user
            user_profile = Profile.objects.get(user=request.user)

            # Tạo hóa đơn mới
            bill = Bill.objects.create(
                table=table,
                customer=user_profile,
                total_price=0,
                is_payed=False
            )
            table.is_occupied = True
            table.current_bill = bill
            table.save()

            return JsonResponse({"success": True, "message": "Đặt bàn thành công!"}, status=200)

        except Table.DoesNotExist:
            return JsonResponse({"success": False, "message": "Không tìm thấy bàn."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Có lỗi xảy ra: {str(e)}"}, status=500)
    else:
        return JsonResponse({"success": False, "message": "Chỉ hỗ trợ phương thức POST."}, status=405)


@csrf_exempt
def cancel_table_api(request, table_id):
    if request.method == 'DELETE':
        try:
            table = Table.objects.get(id=table_id)
            if table.is_occupied:
                # Xóa hóa đơn hiện tại
                table.current_bill.delete()
                table.is_occupied = False
                table.current_bill = None
                table.save()
                return JsonResponse({"success": True, "message": "Hủy đặt bàn thành công!"}, status=200)
            else:
                return JsonResponse({"success": False, "message": "Bàn chưa được đặt."}, status=400)
        except Table.DoesNotExist:
            return JsonResponse({"success": False, "message": "Không tìm thấy bàn."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"success": False, "message": "Chỉ hỗ trợ phương thức DELETE."}, status=405)


@csrf_exempt
def edit_table_api(request, table_id):
    if request.method == 'PUT':
        try:
            table = Table.objects.get(id=table_id)
            if not table.is_occupied:
                return JsonResponse({"success": False, "message": "Bàn chưa được đặt."}, status=400)

            data = json.loads(request.body)
            new_time = data.get('time')
            if not new_time:
                return JsonResponse({"success": False, "message": "Thời gian không hợp lệ."}, status=400)

            # Cập nhật thời gian trong hóa đơn
            bill = table.current_bill
            bill.time = new_time
            bill.save()

            return JsonResponse({"success": True, "message": "Thời gian nhận bàn đã được cập nhật."}, status=200)
        except Table.DoesNotExist:
            return JsonResponse({"success": False, "message": "Không tìm thấy bàn."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"success": False, "message": "Chỉ hỗ trợ phương thức PUT."}, status=405)
