from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import SystemLog

# শুধুমাত্র অ্যাডমিন বা সুপারইউজার এক্সেস পাবে কিনা তা চেক করার হেলপার ফাংশন
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


# ১. সব সিস্টেম অ্যাক্টিভিটি লগ দেখার ভিউ
@user_passes_test(is_admin)
def system_logs_view(request):
    logs = SystemLog.objects.all().order_by('-timestamp')
    return render(request, 'system_admin/system_logs.html', {'logs': logs})


# ২. নির্দিষ্ট কোনো লগের বিস্তারিত দেখা
@user_passes_test(is_admin)
def log_detail_view(request, log_id):
    log = get_object_or_404(SystemLog, id=log_id)
    return render(request, 'system_admin/log_detail.html', {'log': log})


# ৩. পুরাতন লগ ক্লিয়ার করার ভিউ
@user_passes_test(is_admin)
def clear_logs_view(request):
    if request.method == 'POST':
        SystemLog.objects.all().delete()
        messages.success(request, "সমস্ত সিস্টেম লগ সফলভাবে ক্লিয়ার করা হয়েছে।")
        return redirect('system_logs')
    
    return render(request, 'system_admin/clear_logs_confirm.html')