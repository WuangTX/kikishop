from django import forms
from .models import News, NewsCategory


class NewsForm(forms.ModelForm):
    """Form for news article"""
    class Meta:
        model = News
        fields = [
            'category', 'title', 'slug', 'summary', 'content', 'image', 
            'image_position', 'image_caption', 'external_link', 'external_link_text',
            'tags', 'featured', 'status', 'author', 'published_at'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tiêu đề bài viết'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL slug (tự động tạo nếu để trống)'}),
            'summary': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Tóm tắt ngắn gọn về bài viết (tối đa 500 ký tự)',
                'maxlength': 500
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Nội dung chi tiết của bài viết...',
                'style': 'display: none;'  # Hide the original textarea
            }),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image_position': forms.Select(attrs={'class': 'form-control'}),
            'image_caption': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Chú thích cho hình ảnh (tùy chọn)'
            }),
            'external_link': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://example.com'
            }),
            'external_link_text': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Văn bản hiển thị cho liên kết'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'thẻ1, thẻ2, thẻ3 (phân cách bằng dấu phẩy)'
            }),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'published_at': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
        }


class NewsCategoryForm(forms.ModelForm):
    """Form for news category"""
    class Meta:
        model = NewsCategory
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên danh mục'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL slug (tự động tạo nếu để trống)'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Mô tả về danh mục...'
            }),
        }
