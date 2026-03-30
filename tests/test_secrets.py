import pytest
from aegis.detection.secrets import SecretDetector, Detection


class TestSecretDetector:
    @pytest.fixture
    def detector(self):
        return SecretDetector()

    def test_detects_aws_access_key(self, detector):
        text = "My key is AKIAIOSFODNN7EXAMPLE"
        detections = detector.detect(text)
        assert len(detections) >= 1
        assert any(d.entity_type == "AWS_KEY" for d in detections)
        assert any("AKIAIOSFODNN7EXAMPLE" in d.value for d in detections)

    def test_detects_generic_high_entropy_secret(self, detector):
        text = "api_key = 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'"
        detections = detector.detect(text)
        assert len(detections) >= 1

    def test_detects_private_key_block(self, detector):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJBALRE\n-----END RSA PRIVATE KEY-----"
        detections = detector.detect(text)
        assert len(detections) >= 1
        assert any(d.entity_type == "PRIVATE_KEY" for d in detections)

    def test_detects_connection_string(self, detector):
        text = "DATABASE_URL=postgresql://user:pass@host:5432/db"
        detections = detector.detect(text)
        assert len(detections) >= 1

    def test_detects_jwt(self, detector):
        text = "token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        detections = detector.detect(text)
        assert len(detections) >= 1

    def test_no_false_positive_on_normal_text(self, detector):
        text = "This is a normal sentence with no secrets."
        detections = detector.detect(text)
        assert len(detections) == 0

    def test_detects_custom_pattern(self, detector):
        detector.add_custom_pattern("project_id", r"PROJ-[A-Z0-9]{8}")
        text = "Working on PROJ-AB12CD34 today"
        detections = detector.detect(text)
        assert len(detections) >= 1
        assert any(d.entity_type == "project_id" for d in detections)

    def test_detection_has_start_end_offsets(self, detector):
        text = "key is AKIAIOSFODNN7EXAMPLE here"
        detections = detector.detect(text)
        aws = [d for d in detections if d.entity_type == "AWS_KEY"]
        assert len(aws) >= 1
        assert aws[0].start >= 0
        assert aws[0].end > aws[0].start
        assert text[aws[0].start:aws[0].end] == aws[0].value

    def test_detects_prefixed_api_key(self, detector):
        text = "mock token sk-demo-abcdef1234567890"
        detections = detector.detect(text)
        assert any(d.entity_type == "PREFIXED_API_KEY" for d in detections)

    def test_detects_password_in_prose(self, detector):
        text = "set her password to ExamplePass!234"
        detections = detector.detect(text)
        assert any(d.entity_type == "PASSWORD_IN_PROSE" for d in detections)
        pwd = [d for d in detections if d.entity_type == "PASSWORD_IN_PROSE"][0]
        assert "ExamplePass!234" in pwd.value

    def test_detects_international_phone(self, detector):
        text = "phone number +44-7700-900123"
        detections = detector.detect(text)
        assert any(d.entity_type == "PHONE_INTL" for d in detections)

    def test_detects_short_generic_secret(self, detector):
        text = "api-key:abcd1234efgh"
        detections = detector.detect(text)
        assert any(d.entity_type == "GENERIC_SECRET" for d in detections)
