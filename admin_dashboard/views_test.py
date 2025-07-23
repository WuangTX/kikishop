from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

# Check if user is admin/staff
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    """Dashboard trang chủ đơn giản để test"""
    return HttpResponse(f"""
    <html>
    <head><title>Dashboard Test</title></head>
    <body>
        <h1>🎉 Dashboard Works!</h1>
        <p>Xin chào <strong>{request.user.username}</strong>!</p>
        <p>Bạn đã truy cập dashboard thành công!</p>
        <ul>
            <li>Username: {request.user.username}</li>
            <li>Is Staff: {request.user.is_staff}</li>
            <li>Is Superuser: {request.user.is_superuser}</li>
        </ul>
        <a href="/">← Về trang chủ</a>
    </body>
    </html>
    """)
