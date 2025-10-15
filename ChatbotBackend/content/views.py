from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from .chatbot_functions import ask_question

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        from_number = request.POST.get("From", "")
        message_body = request.POST.get("Body", "")
        user_id = from_number

        response_text = ask_question(message_body, user_id)

        resp = MessagingResponse()
        resp.message(response_text)
        return HttpResponse(str(resp), content_type="text/xml")

    return HttpResponse("OK", status=200)

