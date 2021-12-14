from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .models import Item, OrderItem, Order, AddressDetails, Payment, Coupon, Refund
from .forms import CheckoutForm, CouponForm, RefundForm

import random
import string
# Create your views here.

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def register(request):
    form = UserCreationForm

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # username = form.cleaned_data.get('username')
            #
            # messages.success(request, 'Account was created for ' + username)
            # return redirect('login.html')

    context = {'form':form}
    return render(request, 'register.html', context)


def login(request):
    if request.method == 'post':
        username = request.post.get('username')
        password = request.post.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home.html")
        else:
            messages.info(request, 'Username OR password is incorrect')

    context = {}
    return render(request, "accounts:login", context)

class ItemDetailView(DetailView):
    model = Item
    template_name = "products.html"

def products(request):
    context = {
         'items': Item.objects.all()
    }
    return render(request, "products.html", context)

def home(request):
    context = {
         'items': Item.objects.all()
    }
    return render(request, "home.html", context)


def logout_request(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect("logout.html")



class OrderSummaryView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):

		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			context = {
				'object': order
			}
			return render(self.request, "order_summary.html", context)
		except ObjectDoesNotExist:
			messages.error(self.request, "You do not have an active order")
			return redirect("/")



# class CheckoutView(View):
# 	def get(self, *args, **kwargs):
# 		form = CheckoutForm()
# 		# order
# 		order = Order.objects.get(user=self.request.user, ordered=False)
# 		context = {
# 			'form': form,
# 			'order': order
# 		}
# 		return render(self.request, "checkout.html", context)
class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform':CouponForm(),
                'order': order,
                # 'DISPLAY_COUPON_FORM':True
                }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You dont have an active order")
            return redirect("accounts:checkout")


    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                firstname = form.cleaned_data.get('firstname')
                lastname = form.cleaned_data.get('lastname')
                mobilenumber = form.cleaned_data.get('mobilenumber')
                address = form.cleaned_data.get('address')
                town = form.cleaned_data.get('town')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                address_details = AddressDetails(
                user=self.request.user,
                firstname=firstname,
                lastname=lastname,
                mobilenumber=mobilenumber,
                address=address,
                town=town
                )
                address_details.save()
                order.address_details = address_details
                order.save()

                if payment_option == 'M':
                    return redirect('accounts:payment', payment_option='Mobile Money')
                elif payment_option == 'C':
                    return redirect('accounts:payment', payment_option='Cash on Delivery')
                else:
                    messages.warning(self.request, "invalid payment option")
                    return redirect('accounts:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("accounts:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order,
            # 'DISPLAY_COUPON_FORM':False
            }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        amount = int(order.get_total())
        order_items = order.items.all()
        order_items.update(ordered=True)
        order.ordered = True
        order.ref_code = create_ref_code()
        order.save()
        context = {

        'order': order
         }
        messages.success(self.request, "Your order was successfully")
        return render(self.request, "payment.html", context)

        # order_items = order.items.all()
        # order_items.update(ordered=True)
        # for item in order_items:
        #     item.save()
        # create the payment
        # payment = Payment()
        # payment.user = self.request.user
        # payment.amount = int(order.get_total())
        # payment.save()

        # assign the payment to the order
        # order_items = order.items.all()
        # order_items.update(ordered=True)
        # for item in order_items:
        #     item.save()
        #
        # order.ordered = True
        # order.payment = Payment
        # order.save()

class HomeListView(ListView):
    model = Item
    paginate_by = 6
    template_name = "home.html"
    
@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
    item=item,
	user=request.user,
	ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if the order item is in the ordere
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("accounts:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("accounts:order-summary")

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to cart.")
        return redirect("accounts:order-summary")

@login_required
def remove_from_cart(request, slug):
	item = get_object_or_404(Item,slug=slug)
	order_qs = Order.objects.filter(
		user=request.user,
		ordered=False
	)
	if order_qs.exists():
		order = order_qs[0]
		#check if the order item is in the order
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
				item=item,
				user=request.user,
				ordered=False
			)[0]
			order.items.remove(order_item)
			messages.info(request, "This item was removed from cart.")
			return redirect("accounts:order-summary") #core:order-summary
		else:
			messages.info(request, "This item was not in your cart.")
			return redirect("accounts:order-summary")
	else:
		messages.info(request, "You do not have an active order.")
		return redirect("accounts:order-summary")

@login_required
def remove_single_item_from_cart(request, slug):
	item = get_object_or_404(Item,slug=slug)
	order_qs = Order.objects.filter(
		user=request.user,
		ordered=False
	)
	if order_qs.exists():
		order = order_qs[0]
		#check if the order item is in the order
		if order.items.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
				item=item,
				user=request.user,
				ordered=False
			)[0]
			if order_item.quantity > 1:
				order_item.quantity -= 1
				order_item.save()
			else:
				order.items.remove(order_item)
			messages.info(request, "This item quantity was updated.")
			return redirect("accounts:order-summary")
		else:
			messages.info(request, "This item was not in your cart.")
			return redirect("accounts:product", slug=slug)
	else:
		messages.info(request, "You do not have an active order.")
		return redirect("accounts:product", slug=slug)

# coupon
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon doesnot exist")
        return redirect("accounts:checkout")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "successfully added coupon")
                return redirect("accounts:checkout")
            except ObjectDoesNotExist:
                messages.info(request, "you dont have an active order")
                return redirect("accounts:checkout")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
        'form':form
        }
        return render(self.request, "request_refund.html", context)



    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            #edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()
            #store the order
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "your request was received")
                return redirect("accounts:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "your order doesnot exist")
                return redirect("accounts:request-refund")
