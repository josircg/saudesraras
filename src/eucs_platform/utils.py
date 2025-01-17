from django.contrib.messages import get_messages


def get_message_list(request):
    """Returns a list of messages to show in Ajax response, when user press save and continue"""
    if '_continue' in request.POST:
        storage = get_messages(request)
        result = [{'tag': message.tags, 'message': message.message} for message in storage]
    else:
        result = []

    return result
