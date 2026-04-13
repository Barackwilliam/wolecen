from django import forms
from .models import PaymentRequest, PaymentCategory,RequestDocument
from apps.accounts.models import Department

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}

PAYMENT_METHOD_CHOICES = [
    ('', '— Select Method —'),
    ('Bank Transfer', 'Bank Transfer'),
    ('Mobile Money', 'Mobile Money (M-Pesa/Tigo/Airtel)'),
    ('Cash', 'Cash'),
    ('Cheque', 'Cheque'),
    ('RTGS', 'RTGS'),
]


class PaymentRequestForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs=SELECT_ATTRS),
        required=True,
    )

    class Meta:
        model = PaymentRequest
        fields = [
            'title', 'description', 'purpose', 'category', 'priority',
            'amount_requested', 'payment_method', 'needed_by_date',
            'is_advance_payment', 'beneficiary_name', 'beneficiary_bank',
            'beneficiary_account', 'department',
        ]
        widgets = {
            'title': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'e.g. Office Supplies for Q2 Operations'}),
            'description': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Brief description...'}),
            'purpose': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Explain why this payment is necessary...'}),
            'category': forms.Select(attrs=SELECT_ATTRS),
            'priority': forms.Select(attrs=SELECT_ATTRS),
            'amount_requested': forms.NumberInput(attrs={**WIDGET_ATTRS, 'placeholder': '0.00', 'min': '0.01', 'step': '0.01'}),
            'needed_by_date': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'is_advance_payment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'beneficiary_name': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Full name or company name'}),
            'beneficiary_bank': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'e.g. CRDB Bank, NMB Bank'}),
            'beneficiary_account': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'Account number'}),
            'department': forms.Select(attrs=SELECT_ATTRS),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        # Category — optional
        self.fields['category'].queryset = PaymentCategory.objects.filter(is_active=True)
        self.fields['category'].required = False
        self.fields['category'].empty_label = '— Select Category (Optional) —'

        # Department
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = '— Select Department —'

        # Optional fields
        self.fields['needed_by_date'].required = False
        self.fields['beneficiary_name'].required = False
        self.fields['beneficiary_bank'].required = False
        self.fields['beneficiary_account'].required = False

        # Pre-fill and HIDE department if user already has one
        if user and user.department:
            self.fields['department'].initial = user.department.pk
            self.fields['department'].required = False  # not validated from form — set in view
            self.fields['department'].widget = forms.HiddenInput()
            self.initial['department'] = user.department.pk

    def clean(self):
        cleaned = super().clean()
        # If department not submitted (hidden), inject from user
        if self.user and self.user.department and not cleaned.get('department'):
            cleaned['department'] = self.user.department
        return cleaned

    def clean_payment_method(self):
        method = self.cleaned_data.get('payment_method', '').strip()
        if not method:
            raise forms.ValidationError('Please select a payment method.')
        return method


class CommentForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3, 'placeholder': 'Enter your comment...'}),
        required=True,
    )
    is_internal = forms.BooleanField(required=False)


class RetirementForm(forms.Form):
    amount_actual = forms.DecimalField(
        widget=forms.NumberInput(attrs={**WIDGET_ATTRS, 'step': '0.01'}),
        min_value=0,
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        required=False,
    )


class RequestDocumentAdminForm(forms.ModelForm):
    class Meta:
        model = RequestDocument
        fields = '__all__'
        widgets = {
            'avatar': forms.TextInput(attrs={
                'role': 'uploadcare-uploader',
                'data-public-key': '431f160fc3fcf0ffb783',
                'data-images-only': 'true',
            })
        }

    class Media:
        css = {
            'all': ['https://ucarecdn.com/libs/widget/3.x/uploadcare.min.css']
        }
        js = [
            'https://ucarecdn.com/libs/widget/3.x/uploadcare.full.min.js',
        ]