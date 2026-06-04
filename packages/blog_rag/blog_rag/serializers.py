"""
DRF serializers that validate and clean incoming request data for each view.

ChatRequestSerializer  — validates POST body for ChatView.
SearchQuerySerializer  — validates query-string params for SearchView.
"""

from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """
    Validates the JSON body sent to POST /chat/.

    Fields:
        message     — the user's question (required, max 2000 chars).
        link        — URL of the blog page the user is currently viewing
                      (optional). When present it is appended to the message
                      so the agent knows the page context.
        session_id  — opaque string that identifies the conversation thread
                      (optional). If omitted, ChatView generates a new UUID
                      so every call starts a fresh session.
    """
    message = serializers.CharField(max_length=2000)
    link = serializers.URLField(required=False)
    session_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class SearchQuerySerializer(serializers.Serializer):
    """
    Validates query-string parameters for GET /search/.

    Fields:
        q  — the search query text (required, max 500 chars).
        k  — number of results to return (optional, 1–20, defaults to TOP_K
             from settings if omitted).
    """

    q = serializers.CharField(max_length=500)
    k = serializers.IntegerField(min_value=1, max_value=20, required=False)
