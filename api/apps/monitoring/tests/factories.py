"""
Factories for monitoring-related tests.
Using Factory Boy to generate test data.
"""

import factory  # type: ignore
from django.utils import timezone

from api.apps.monitoring.models import ErrorLog, RequestLog


class RequestLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating test RequestLog instances"""

    class Meta:
        model = RequestLog

    path = factory.Sequence(lambda n: f"/api/test/endpoint/{n}")
    method = "GET"
    response_time = factory.Faker("pyfloat", min_value=0.001, max_value=2.0)
    status_code = 200
    user_id = factory.Sequence(lambda n: f"user_{n}")
    ip_address = factory.Faker("ipv4")
    timestamp = factory.LazyFunction(timezone.now)
    request_data = factory.Dict(
        {"param1": factory.Sequence(lambda n: f"value_{n}"), "param2": "test"}
    )
    response_data = factory.Dict(
        {
            "status": "success",
            "data": factory.Sequence(lambda n: f"response_{n}"),
        }
    )


class ErrorLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating test ErrorLog instances"""

    class Meta:
        model = ErrorLog

    timestamp = factory.LazyFunction(timezone.now)
    error_type = factory.Iterator(["ValidationError", "404", "500", "PermissionDenied"])
    error_message = factory.Faker("sentence")
    traceback = factory.Faker("text")
    path = factory.Sequence(lambda n: f"/api/test/error/{n}")
    method = factory.Iterator(["GET", "POST", "PUT", "DELETE"])
    user_id = factory.Sequence(lambda n: f"user_{n}")
    request_data = factory.Dict(
        {"error_param": factory.Sequence(lambda n: f"error_value_{n}")}
    )
    url = factory.Sequence(lambda n: f"http: //testserver/api/test/error/{n}")
