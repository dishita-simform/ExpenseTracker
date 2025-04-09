from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Expense, Category, Income, IncomeSource, Budget, CATEGORIES
from django.utils import timezone

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense description'}),
            'category': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            
            # Set default date to today if not provided
            if not self.instance.pk and not self.data.get('date'):
                self.initial['date'] = timezone.now().date()
                
            # Set max date to today
            self.fields['date'].widget.attrs['max'] = timezone.now().date().strftime('%Y-%m-%d')
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Expense date cannot be in the future.")
        return date

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['source', 'amount', 'description', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter income description'}),
            'source': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Get user's income sources from the database
            sources = IncomeSource.objects.filter(user=user)
            # Create choices list with sources from the database
            choices = [(source.id, source.name) for source in sources]
            self.fields['source'].choices = choices
            
            # Set default date to today if not provided
            if not self.instance.pk and not self.data.get('date'):
                self.initial['date'] = timezone.now().date()
                
            # Set max date to today
            self.fields['date'].widget.attrs['max'] = timezone.now().date().strftime('%Y-%m-%d')
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        current_date = timezone.now().date()
        if date and date > current_date:
            raise forms.ValidationError('Income date cannot be in the future.')
        
        return date

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Get user's categories from the database
            categories = Category.objects.filter(user=user)
            # Create choices list with categories from the database
            choices = [(cat.id, cat.name) for cat in categories]
            self.fields['category'].choices = choices
            
            # Set default start date to today if not provided
            if not self.instance.pk and not self.data.get('start_date'):
                self.initial['start_date'] = timezone.now().date()
                
            # Set max date to today for start_date
            self.fields['start_date'].widget.attrs['max'] = timezone.now().date().strftime('%Y-%m-%d')
            
            # Make end_date optional
            self.fields['end_date'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('End date cannot be before start date.')
        
        return cleaned_data 