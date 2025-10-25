import datetime
import json
from traceback import print_exception

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from Channels.models import Channel
from Messenger.models import Post
from NoGraph.utils import check_jwt, extract_token
from Register.models import CustomUser


# General
@csrf_exempt
async def create_channel(request):
    if not request.method == "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    token_data = check_jwt(extract_token(request))
    data = json.loads(request.body.decode('utf-8'))
    initiator = data.get('initiator')
    if not initiator or type(initiator) != str or not str(initiator).__contains__('@'):
        return JsonResponse({'status': 'error', 'message': 'Invalid initiator. \nPlease enter an registered email'}, status=400)
    targets_str = data.get('targets')# e.g. 123@gmail.com,456@outlook.com
    if not targets_str or not type(targets_str)==str or not targets_str.__contains__('@'):
        return JsonResponse({'status': 'error', 'message': 'Invalid targets.'}, status=400)
    targets = targets_str.split(',')
    if not targets:
        return JsonResponse({'status': 'error', 'message': 'Invalid input format for targets.'}, status=400)
    for t in targets:
        if t.count('@') != 1:
            return JsonResponse({'status': 'error', 'message': 'Invalid targets.'}, status=400)
    name = data.get('name')
    if not name or type(name) != str:
        return JsonResponse({'status': 'error', 'message': 'Invalid channel name.'}, status=400)
    try:
        # Check validity of initiator
        init_user = await CustomUser.objects.aget(email=initiator)
        if not token_data or token_data ['user_id'] != init_user.email or not init_user.is_active:
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
        # Find as many as possible target members, a user must be at least registered to be invited
        mem = []
        for t in targets:
            tar_usr = await CustomUser.objects.aget(email=t)
            if not tar_usr:
                continue
            else:
                mem.append(tar_usr)
        # No explicit leader
        mem.append(init_user)
        # Inject the fields
        channel, created = await Channel.objects.aget_or_create(name = name)
        if not created:
            return JsonResponse({'status': 'error', 'message': 'Channel already exists.'}, status=400)
        for m in mem:
            await channel.members.aadd(m)
        channel.created_at = timezone.now()
        channel.updated_at = timezone.now()
        await sync_to_async(channel.save)()
        return JsonResponse({'status': 'success', 'message': 'Channel created successfully.'}, status=200)
    except Exception as e:
        print_exception( e)
        return JsonResponse({'status': 'error', 'message': "An err occurred"+str(e)}, status=500)
