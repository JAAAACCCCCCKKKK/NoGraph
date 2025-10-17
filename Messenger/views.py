import json
from traceback import print_exception

from asgiref.sync import sync_to_async
from django.db.models import Max

from Register.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from Channels.models import Channel
from Messenger.models import Post, Plain, Vote
from NoGraph.utils import check_jwt, extract_token


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
        user = await CustomUser.objects.aget(email=eml)
        if not user or not user.is_active or not token_data or not token_data['user_id']==eml :
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        channel = await Channel.objects.aget(name =  cha)
        if not channel or not (await channel.members.aget(email=eml)):
            return JsonResponse({'status': 'error', 'message': 'please join or create the channel'}, status=400)
        if not con or not type(con)==str:
            return JsonResponse({'status': 'error', 'message': 'content is required'}, status=400)
        typ = data.get('type')
        if not typ or not typ in ['plain', 'vote']:
            return JsonResponse({'status': 'error', 'message': 'invalid type'}, status=400)
        max_in_channel_id = await sync_to_async(
            lambda: Post.objects.filter(channel=channel)
                    .aggregate(Max('in_channel_id'))['in_channel_id__max'] or 0
        )()
        message= await Post.objects.acreate(channel = channel, sender = user, post_type = typ, in_channel_id = max_in_channel_id + 1)
        if typ =='plain':
            p = await Plain.objects.acreate(post = message, content = con)
            await sync_to_async(p.save)()
        elif typ =='vote':
            v=await Vote.objects.acreate(post = message, description = con)
            await sync_to_async(v.save)()
        await sync_to_async(message.save)()
        return JsonResponse({'status': 'success', 'message': 'message sent successfully'}, status=200)
    except Exception as e:
        print_exception(e)
        return JsonResponse({'status': 'error', 'message': "An error occurred"+str(e)}, status=500)

@csrf_exempt
async def make_vote(request):
    if not request.method == "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    eml = data.get('email')
    cha = data.get('channel')
    post = data.get('post') # in_channel_id
    option = data.get('option')
    token_data = check_jwt(extract_token(request))
    #validate
    if not eml or not type(eml)==str or not eml.__contains__("@"):
        return JsonResponse({'status': 'error', 'message': 'invalid email'}, status=400)
    if not cha or not type(cha)==str:
        return JsonResponse({'status': 'error', 'message': 'channel is required'}, status=400)
    if not post or not type(post)==int:
        return JsonResponse({'status': 'error', 'message': 'in channel post id is required'}, status=400)
    if option is None or not type(option) == bool:
        return JsonResponse({'status': 'error', 'message': 'option is required'}, status=400)
    try:
        user = await CustomUser.objects.aget(email=eml)
        if not user or not user.is_active or not token_data or not token_data['user_id']==eml :
            return JsonResponse({'status': 'error', 'message': 'please log in'}, status=400)
        channel = await Channel.objects.aget(name =  cha)
        if not channel or not (await channel.members.aget(email=eml)):
            return JsonResponse({'status': 'error', 'message': 'please join or create the channel'}, status=400)
        message = await Post.objects.aget(channel = channel, in_channel_id = post)
        if not message or not message.post_type == 'vote':
            return JsonResponse({'status': 'error', 'message': 'vote post not found'}, status=404)
        vote_obj = await Vote.objects.aget(post=message)
        if not vote_obj:
            return JsonResponse({'status': 'error', 'message': 'vote post not found'}, status=404)
        if await sync_to_async(lambda: vote_obj.voted_users.filter(email=eml).exists())():
            return JsonResponse({'status': 'error', 'message': 'you have already voted to this post'}, status=400)
        if option:
            vote_obj.supporting_votes += 1
        else:
            vote_obj.opposing_votes += 1
        await vote_obj.voted_users.aadd(user)
        await sync_to_async(vote_obj.save)()
        return JsonResponse({'status': 'success', 'message': 'vote recorded successfully'}, status=200)
    except Exception as e:
        print_exception(e)
        return JsonResponse({'status': 'error', 'message': "An error occurred"+str(e)}, status=500)




