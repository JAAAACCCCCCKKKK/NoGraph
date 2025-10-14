import json

from asgiref.sync import sync_to_async
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from Channels.models import Channel
from Messenger.models import post
from NoGraph.utils import check_jwt, extract_token
from Register.models import User


# Create your views here.

@csrf_exempt
async  def send_message(request):
    if not request.method == "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    cha = data.get('channel')
    con = data.get('content')
    token_data = check_jwt(extract_token(request))
    try:
        user = await User.objects.aget(email=eml)
        if not user or not user.active or not check_jwt(token_data) or not token_data['user_id']==eml :
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        channel = await Channel.objects.aget(name =  cha)
        if not channel or not channel.members.filter(email=eml).exists():
            return JsonResponse({'status': 'error', 'message': 'please join or create the channel'}, status=400)
        if not con or not type(con)==dict:
            return JsonResponse({'status': 'error', 'message': 'content is required'}, status=400)
        typ = con.get('type')
        if not typ or not typ in ['plain', 'vote']:
            return JsonResponse({'status': 'error', 'message': 'invalid type'}, status=400)
        max_in_channel_id = max([p.in_channel_id for p in await post.objects.filter(channel = channel).order_by('in_channel_id')])
        message= post.objects.create(channel = channel, sender = user, content = con, in_channel_id = max_in_channel_id + 1)
        con['post']= message.id
        await sync_to_async(message.save)()
        await sync_to_async(con.save)()
        return JsonResponse({'status': 'success', 'message': 'message sent successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': "An error occurred"+str(e)}, status=500)

@csrf_exempt
async def compose_message(request):
    # 生成对应种类的消息并以Json格式返回调用方，调用方可以选择编辑（重新生成）
    pass



