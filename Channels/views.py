import datetime
import json

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from Channels.models import Channel
from Messenger.models import post
from NoGraph.utils import check_jwt, extract_token
from Register.models import User


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
        init_user = await User.objects.aget(email=initiator)
        if not check_jwt(token_data) or not init_user.active:
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
        # Find as many as possible target members, a user must be at least registered to be invited
        mem = []
        for t in targets:
            tar_usr = await User.objects.aget(email=t)
            if not tar_usr:
                continue
            else:
                mem.append(tar_usr)
        # No explicit leader
        mem.append(init_user)
        # Inject the fields
        channel, created = Channel.objects.get_or_create(name = name)
        if not created:
            return JsonResponse({'status': 'error', 'message': 'Channel already exists.'}, status=400)
        for m in mem:
            channel.members.add(m)
        channel.created_at = timezone.now()
        channel.updated_at = timezone.now()
        await sync_to_async(channel.save)()
        return JsonResponse({'status': 'success', 'message': 'Channel created successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': "An err occurred"+str(e)}, status=500)

@csrf_exempt
async def read_channel(request):
    if not request.method == "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    token_data = check_jwt(extract_token(request))
    data = json.loads(request.body.decode('utf-8'))
    current_user = data.get('usr')
    channel_name = data.get('channel')
    start_line = data.get('start_line')
    end_line = data.get('end_line')
    if not start_line or not end_line or type(start_line) != int or type(end_line) != int or start_line > end_line or end_line - start_line > 100:
        return JsonResponse({'status': 'error', 'message': 'Invalid line numbers.'}, status=400)
    if not current_user:
        return JsonResponse({'status': 'error', 'message': 'Invalid current user.'}, status=403)
    try:
        usr = await User.objects.aget(email=current_user)
        if not usr or not usr.active or not token_data or not token_data['user_id']==usr.email:
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
        # Check if the user is in the channel
        channel = await Channel.objects.aget(name = channel_name)
        if not channel:
            return JsonResponse({'status': 'error', 'message': 'Channel not found.'}, status=404)
        if usr not in channel.members:
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
        posts = await post.objects.filter(channel = channel, in_channel_id__range=[start_line, end_line]).order_by('in_channel_id')
        posts_resp = []
        max_post_id_in_this_channel = max([p.in_channel_id for p in posts])
        for p in posts:
            posts_resp.append({
                'channel': p.channel.name,
                'sender': p.sender.email,
                'content': p.content,
                'created_at': p.created_at,
                'type': p.tYpe,
                'latest_id': max_post_id_in_this_channel,
            })
        return JsonResponse({'status': 'success', 'message': 'Posts retrieved successfully.', 'posts': posts_resp}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': "An error occurred"+str(e)}, status=500)
