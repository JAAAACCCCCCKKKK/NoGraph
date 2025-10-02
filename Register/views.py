import json
import random
import string

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import User
from NoGraph.utils import create_jwt, check_jwt
from NoGraph import settings


# General

@csrf_exempt
async def Register(request):
    if request.method != "POST":
        # print(request.GET["abc"])
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    usr = data.get('username')
    eml = data.get('email')
    code = data.get('code')
    if not usr or not eml or not code:
        return JsonResponse({'status': 'error', 'message': 'Username, email, and code are required.'}, status=400)

    session_code = await sync_to_async(request.session.get)(f"email_code_{eml}")
    code_expire  = await sync_to_async(request.session.get)(f"code_expire_{eml}")

    if not session_code or session_code != code or int(timezone.now().timestamp()) > code_expire:
        request.session['code_expire'] = -1  # 使验证码失效
        return JsonResponse({'status': 'error', 'message': 'Invalid or expired verification code.'}, status=400)

    user, created = await User.objects.aget_or_create(email=eml, defaults={'username': usr})
    if user.username != usr:
        request.session['code_expire'] = -1  # 使验证码失效
        return JsonResponse({'status': 'error', 'message': 'Email already registered with a different username.'}, status=400)
    user.active = True
    user.updated_at = timezone.now()
    await sync_to_async(user.save)()
    tok = create_jwt(eml, user.is_admin)

    if created:
        request.session['code_expire'] = -1  # 使验证码失效
        return JsonResponse({'status': 'success', 'message': f'User registered as {usr} successfully.', 'token':tok}, status=200)
    else:
        request.session['code_expire'] = -1  # 使验证码失效
        return JsonResponse({'status': 'success', 'message': f'User logged in as {usr} successfully.', 'token':tok}, status=200)

@csrf_exempt
async def SendCode(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

    eml = data.get("email")
    if not eml:
        return JsonResponse({"status": "error", "message": "Email is required."}, status=400)

    # 生成 6 位验证码
    verification_code = ''.join(random.choices(string.digits, k=6))
    expire_ts = int(timezone.now().timestamp() + 90)  # 1.5 分钟过期

    # 用 sync_to_async 保存到 session
    await sync_to_async(request.session.__setitem__)(f"email_code_{eml}", verification_code)
    await sync_to_async(request.session.__setitem__)(f"code_expire_{eml}", expire_ts)

    try:
        # 异步执行发送邮件
        await sync_to_async(send_mail)(
            subject='Your Verification Code',
            message=f'Your verification code is: {verification_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[eml],
            fail_silently=False,
        )
        return JsonResponse({'status': 'success', 'message': 'Verification code sent successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to send email: {str(e)}'}, status=500)

@csrf_exempt
async def Logout(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    if not eml:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        user = await User.objects.aget(email=eml)
        if not user.active or check_jwt(request.META.get('AUTH', '').split(' ')[-1])['user_id'] != eml:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        user.active = False
        user.updated_at = timezone.now()
        await sync_to_async(user.save)()
        return JsonResponse({'status': 'success', 'message': 'User logged out successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
async def ChangeName(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    new_name = data.get('new_username')
    if not eml or not new_name:
        return JsonResponse({'status': 'error', 'message': 'Email and new username are required.'}, status=400)
    try:
        user = await User.objects.aget(email=eml)
        if not user.active or check_jwt(request.META.get('AUTH', '').split(' ')[-1])['user_id'] != eml:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        user.username = new_name
        user.updated_at = timezone.now()
        await sync_to_async(user.save)()
        return JsonResponse({'status': 'success', 'message': 'Username changed successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
async def GetPtf(request):
    if request.method != "GET":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    eml = request.GET['email']
    if not eml:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        user = await User.objects.aget(email=eml)
        if not user.active or check_jwt(request.META.get('AUTH', '').split(' ')[-1])['user_id'] != eml:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        return JsonResponse({'status': 'success', 'username': user.username, 'email': user.email, 'created_at':user.created_at}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

# Operators only

# Super operators only
@csrf_exempt
async def OpPrivOnOff(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    target = data.get('target_email')
    if not target:
        return JsonResponse({'status': 'error', 'message': 'Target email is required.'}, status=400)
    if not eml:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        user = await User.objects.aget(email=eml)
        target_user = await User.objects.aget(email=target)
        if (not user.active
                or check_jwt(request.META.get('AUTH', '').split(' ')[-1])['user_id'] != eml
                or user not in settings.SUPER_OPERATORS):
            return JsonResponse({'status': 'error', 'message': 'please log in as super operator'}, status=400)
        target_user.is_admin = not target_user.is_admin
        target_user.updated_at = timezone.now()
        await sync_to_async(target_user.save)()
        return JsonResponse({'status': 'success', 'message': f'User {target_user.username} operator privilege is now {target_user.is_admin}.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)