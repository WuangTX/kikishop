from django import forms
from customer_web.models import ProductInventory, Product


class ProductInventoryForm(forms.ModelForm):
    """Form for managing product inventory by size and color"""
    
    class Meta:
        model = ProductInventory
        fields = ['product', 'size', 'color', 'quantity']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'size': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'color': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True,
                'placeholder': 'Nhập số lượng'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['product'].empty_label = "Chọn sản phẩm..."
        self.fields['size'].empty_label = "Chọn size..."
        self.fields['color'].empty_label = "Chọn màu sắc..."
        

class BulkInventoryForm(forms.Form):
    """Form for bulk updating inventory"""
    OPERATION_CHOICES = [
        ('set', 'Đặt thành'),
        ('add', 'Tăng thêm'),
        ('subtract', 'Giảm đi')
    ]
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        empty_label="Chọn sản phẩm...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label="Sản phẩm"
    )
    
    sizes = forms.MultipleChoiceField(
        choices=ProductInventory.SIZE_CHOICES,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5',
            'required': True
        }),
        label="Size"
    )
    
    colors = forms.MultipleChoiceField(
        choices=ProductInventory.COLOR_CHOICES,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5',
            'required': True
        }),
        label="Màu sắc"
    )
    
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label="Thao tác"
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'required': True,
            'placeholder': 'Số lượng'
        }),
        label="Số lượng"
    )
