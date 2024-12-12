from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.contrib.auth.decorators import permission_required

from django.shortcuts import get_object_or_404,redirect
from django.http import HttpResponseRedirect
import datetime

from .forms import RenewBookForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import Reservation

from django.http import HttpResponseForbidden


def confirm_reservation(request, reservation_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.status = 'confirmed'
    reservation.save()
    return redirect('reservation_list')


def reject_reservation(request, reservation_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.status = 'rejected'
    reservation.save()
    return redirect('reservation_list')


def reservation_list(request):
    if request.user.is_staff:
        reservations = Reservation.objects.filter(status='pending')
        return render(request, 'catalog/reservation_list.html', {'reservation': reservations})

    else:
        return redirect('index')


def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_books_title = Book.objects.filter(title__icontains='души').count()
    num_authors = Author.objects.count()
    num_genre = Genre.objects.all().count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1


    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available,
                 'num_authors': num_authors, 'num_genre': num_genre,
                 'num_books_title': num_books_title, 'num_visits': num_visits},
    )


class BookListView(generic.ListView):
    model = Book
    paginate_by = 2


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back'))


class LoanedBooksByStaffListView(PermissionRequiredMixin,generic.ListView):
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_staff.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')



@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':


        form = RenewBookForm(request.POST)


        if form.is_valid():

            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()


            return HttpResponseRedirect('/')

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):
    model = Book
    fields = '__all__'


class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'


class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')