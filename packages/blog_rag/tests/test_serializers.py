import pytest
from blog_rag.serializers import ChatRequestSerializer, SearchQuerySerializer


class TestChatRequestSerializer:
    def test_valid_message(self):
        s = ChatRequestSerializer(data={"message": "what is rate limiting?"})
        assert s.is_valid()

    def test_message_required(self):
        s = ChatRequestSerializer(data={})
        assert not s.is_valid()
        assert "message" in s.errors

    def test_message_max_length(self):
        s = ChatRequestSerializer(data={"message": "x" * 2001})
        assert not s.is_valid()
        assert "message" in s.errors

    def test_optional_fields_absent(self):
        s = ChatRequestSerializer(data={"message": "hello"})
        assert s.is_valid()
        assert s.validated_data.get("link") is None
        assert s.validated_data.get("session_id") is None

    def test_valid_link(self):
        s = ChatRequestSerializer(data={
            "message": "hello",
            "link": "https://blog.example.com/post",
        })
        assert s.is_valid()

    def test_invalid_link(self):
        s = ChatRequestSerializer(data={"message": "hello", "link": "not-a-url"})
        assert not s.is_valid()
        assert "link" in s.errors

    def test_session_id_passed_through(self):
        s = ChatRequestSerializer(data={"message": "hello", "session_id": "abc-123"})
        assert s.is_valid()
        assert s.validated_data["session_id"] == "abc-123"


class TestSearchQuerySerializer:
    def test_valid_query(self):
        s = SearchQuerySerializer(data={"q": "nginx config"})
        assert s.is_valid()

    def test_q_required(self):
        s = SearchQuerySerializer(data={})
        assert not s.is_valid()
        assert "q" in s.errors

    def test_k_is_optional(self):
        s = SearchQuerySerializer(data={"q": "nginx"})
        assert s.is_valid()
        assert "k" not in s.validated_data

    def test_k_valid_range(self):
        s = SearchQuerySerializer(data={"q": "nginx", "k": 10})
        assert s.is_valid()
        assert s.validated_data["k"] == 10

    def test_k_below_min(self):
        s = SearchQuerySerializer(data={"q": "nginx", "k": 0})
        assert not s.is_valid()
        assert "k" in s.errors

    def test_k_above_max(self):
        s = SearchQuerySerializer(data={"q": "nginx", "k": 21})
        assert not s.is_valid()
        assert "k" in s.errors
