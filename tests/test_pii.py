import pytest
from aegis.detection.pii import PiiDetector, Detection


class TestPiiDetector:
    @pytest.fixture
    def detector(self):
        return PiiDetector()

    def test_detects_email(self, detector):
        text = "Contact me at john.doe@example.com please"
        detections = detector.detect(text)
        assert any(d.entity_type == "EMAIL_ADDRESS" for d in detections)
        email_det = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"][0]
        assert email_det.value == "john.doe@example.com"

    def test_detects_phone_number(self, detector):
        text = "Call me at 555-123-4567"
        detections = detector.detect(text)
        assert any(d.entity_type == "PHONE_NUMBER" for d in detections)

    def test_detects_credit_card(self, detector):
        text = "Card number: 4111 1111 1111 1111"
        detections = detector.detect(text)
        assert any(d.entity_type == "CREDIT_CARD" for d in detections)

    def test_detects_ip_address(self, detector):
        text = "Server at 192.168.1.100 is down"
        detections = detector.detect(text)
        assert any(d.entity_type == "IP_ADDRESS" for d in detections)

    def test_no_false_positive_on_clean_text(self, detector):
        text = "The function returns a list of integers."
        detections = detector.detect(text)
        assert len(detections) == 0

    def test_detection_has_offsets(self, detector):
        text = "Email: test@example.com"
        detections = detector.detect(text)
        email_det = [d for d in detections if d.entity_type == "EMAIL_ADDRESS"]
        assert len(email_det) >= 1
        d = email_det[0]
        assert d.start >= 0
        assert d.end > d.start
        assert text[d.start:d.end] == d.value
