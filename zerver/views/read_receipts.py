from django.http.request import HttpRequest
from django.http.response import HttpResponse

from zerver.lib.message import access_message
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_success
from zerver.lib.validator import to_non_negative_int
from zerver.models import UserMessage, UserProfile


@has_request_variables
def read_receipts(
    request: HttpRequest,
    user_profile: UserProfile,
    message_id: int = REQ(converter=to_non_negative_int, path_only=True),
) -> HttpResponse:

    # Verify user has access to message.
    message = access_message(user_profile, message_id)[0]

    user_ids = (
        UserMessage.objects.filter(
            message_id=message_id,
            user_profile__is_active=True,
            user_profile__send_read_receipts=True,
        )
        .exclude(user_profile_id=message.sender_id)
        .extra(
            where=[UserMessage.where_read()],
        )
        .values_list("user_profile_id", flat=True)
    )

    return json_success(request, {"user_ids": list(user_ids)})
