import json
from datetime import datetime, timezone, timedelta
import responses
from fcache.cache import FileCache
from tests.utilities.testing_constants import URL, APP_NAME, INSTANCE_ID, CUSTOM_HEADERS, CUSTOM_OPTIONS, IP_LIST
from UnleashClient.constants import METRICS_URL, METRIC_LAST_SENT_TIME
from UnleashClient.periodic_tasks import aggregate_and_send_metrics
from UnleashClient.features import Feature
from UnleashClient.strategies import RemoteAddress, Default


FULL_METRICS_URL = URL + METRICS_URL
print(FULL_METRICS_URL)


@responses.activate
def test_aggregate_and_send_metrics():
    responses.add(responses.POST, FULL_METRICS_URL, json={}, status=200)

    start_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    cache = FileCache("TestCache")
    cache[METRIC_LAST_SENT_TIME] = start_time
    strategies = [RemoteAddress(parameters={"IPs": IP_LIST}), Default()]
    my_feature1 = Feature("My Feature1", True, strategies)
    my_feature1.yes_count = 1
    my_feature1.no_count = 1

    my_feature2 = Feature("My Feature2", True, strategies)
    my_feature2.yes_count = 2
    my_feature2.no_count = 2

    my_feature3 = Feature("My Feature3", True, strategies)
    my_feature3.yes_count = 0
    my_feature3.no_count = 0

    features = {"My Feature1": my_feature1, "My Feature 2": my_feature2}

    aggregate_and_send_metrics(URL, APP_NAME, INSTANCE_ID, CUSTOM_HEADERS, CUSTOM_OPTIONS, features, cache)

    assert len(responses.calls) == 1
    request = json.loads(responses.calls[0].request.body)

    assert len(request['bucket']["toggles"].keys()) == 2
    assert request['bucket']["toggles"]["My Feature1"]["yes"] == 1
    assert request['bucket']["toggles"]["My Feature1"]["no"] == 1
    assert "My Feature3" not in request['bucket']["toggles"].keys()
    assert cache[METRIC_LAST_SENT_TIME] > start_time


@responses.activate
def test_no_metrics():
    responses.add(responses.POST, FULL_METRICS_URL, json={}, status=200)

    start_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    cache = FileCache("TestCache")
    cache[METRIC_LAST_SENT_TIME] = start_time
    strategies = [RemoteAddress(parameters={"IPs": IP_LIST}), Default()]

    my_feature1 = Feature("My Feature1", True, strategies)
    my_feature1.yes_count = 0
    my_feature1.no_count = 0

    features = {"My Feature1": my_feature1}

    aggregate_and_send_metrics(URL, APP_NAME, INSTANCE_ID, CUSTOM_HEADERS, CUSTOM_OPTIONS, features, cache)

    assert len(responses.calls) == 0
