import json
import random
import string
import traceback

from asgiref.sync import sync_to_async
from django.conf import settings
from Register.models import CustomUser as User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from Channels.models import Channel
from NoGraph.utils import create_jwt, check_jwt, extract_token
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
    user.is_active = True
    user.last_login = timezone.now()
    user.updated_at = timezone.now()
    await sync_to_async(user.save)()
    tok = create_jwt(eml)

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
    if not eml or not type(eml)==str or not str(eml).__contains__("@"):
        return JsonResponse({"status": "error", "message": "Email is missing or invalid"}, status=400)

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
            message=f'Your verification code is: {verification_code}, please do not share this code with anyone.',
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
        user = await sync_to_async( User.objects.get)(email=eml)
        token_data = check_jwt(extract_token(request))
        print(timezone.now().timestamp())
        if not token_data or not token_data['user_id'] == eml or not user.is_active:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        user.updated_at = timezone.now()
        user.is_active = False
        await sync_to_async(user.save)()
        return JsonResponse({'status': 'success', 'message': 'User logged out successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        print(e)
        traceback.print_exc()
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
        user = await sync_to_async(User.objects.get)(email=eml)
        token_data = check_jwt(extract_token(request))
        if not token_data or not token_data['user_id'] == eml or not user.is_active:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        user.username = new_name
        await sync_to_async(user.save)()
        return JsonResponse({'status': 'success', 'message': 'Username changed successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
async def GetPtf(request):
    if request.method != "GET":
        return JsonResponse({'status': 'error', 'message': 'Only GET allowed.'}, status=405)
    eml = request.GET['email']
    if not eml:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    try:
        user = await User.objects.aget(email=eml)
        token_data = check_jwt(extract_token(request))
        if not token_data or token_data['user_id'] != eml or not user.is_active:
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        return JsonResponse({'status': 'success', 'username': user.username, 'email': user.email}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)

# Operators only
# TODO : 管理员鉴权
@csrf_exempt
async def BanUser(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    if not eml:
        return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)
    target = data.get('target')
    if not target:
        return JsonResponse({'status': 'error', 'message': 'Target is required.'}, status=400)
    try:
        user = await sync_to_async(User.objects.get)(email=eml)
        token_data = check_jwt(extract_token(request))
        if not token_data or not token_data['user_id'] == eml or not user.is_active or not user.is_staff:
            return JsonResponse({'status': 'error', 'message': 'please log in as operator'}, status=400)
        target_usr = await sync_to_async(User.objects.get)(email=target)
        involved_cnl = await sync_to_async(lambda: list(Channel.objects.filter(members=target_usr).values_list('name', flat=True)))()
        for channel in involved_cnl:
            await sync_to_async(channel.members.remove)(target_usr)
        await sync_to_async(target_usr.delete)()
        await sync_to_async(target_usr.save)()
        return JsonResponse({'status': 'success', 'message': 'Target deleted successfully.'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User does not exist.'}, status=404)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'}, status=500)
