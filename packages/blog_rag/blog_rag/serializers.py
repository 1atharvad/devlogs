from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    k = serializers.IntegerField(min_value=1, max_value=20, required=False)
