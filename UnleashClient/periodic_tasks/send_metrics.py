from collections import ChainMap
from datetime import datetime, timezone
from fcache.cache import FileCache
from UnleashClient.api import send_metrics
from UnleashClient.constants import METRIC_LAST_SENT_TIME
from UnleashClient.utils import LOGGER


def aggregate_and_send_metrics(url: str,
                               app_name: str,
                               instance_id: str,
                               custom_headers: dict,
                               custom_options: dict,
                               features: dict,
                               ondisk_cache: FileCache
                               ) -> None:
    feature_stats_list = []

    for feature_name in features.keys():
        if not (features[feature_name].yes_count or features[feature_name].no_count):
            continue

        feature_stats = {
            features[feature_name].name: {
                "yes": features[feature_name].yes_count,
                "no": features[feature_name].no_count
            }
        }

        features[feature_name].reset_stats()
        feature_stats_list.append(feature_stats)

    metrics_request = {
        "appName": app_name,
        "instanceId": instance_id,
        "bucket": {
            "start": ondisk_cache[METRIC_LAST_SENT_TIME].isoformat(),
            "stop": datetime.now(timezone.utc).isoformat(),
            "toggles": dict(ChainMap(*feature_stats_list))
        }
    }

    if feature_stats_list:
        send_metrics(url, metrics_request, custom_headers, custom_options)
        ondisk_cache[METRIC_LAST_SENT_TIME] = datetime.now(timezone.utc)
        ondisk_cache.sync()
    else:
        LOGGER.debug("No feature flags with metrics, skipping metrics submission.")
