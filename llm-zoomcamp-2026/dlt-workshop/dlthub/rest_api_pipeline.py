from typing import Any, Optional

import dlt
from dlt.common.pendulum import pendulum
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources


@dlt.source(name="logfire")
def logfire_source(
    read_token: Optional[str] = dlt.secrets.value,
    base_url: str = dlt.config.value,
    min_timestamp: Optional[str] = None,
) -> Any:
    """Load data from the Pydantic Logfire Query API (https://logfire.pydantic.dev/docs/).

    The API exposes a single endpoint (POST /v2/query) that runs a SQL query
    against your project's data. This resource pulls the `records` table,
    which holds spans/traces.

    Args:
        read_token: Logfire read token (generated in the Logfire web UI/CLI).
            Auto-loaded from secrets.toml.
        base_url: Region base URL, e.g. "https://logfire-us.pydantic.dev/" or
            "https://logfire-eu.pydantic.dev/". Auto-loaded from config.toml.
        min_timestamp: ISO8601 lower bound for `start_timestamp` (required by
            the API). Defaults to 7 days ago.

    Example:
        pipeline.run(logfire_source())
        pipeline.run(logfire_source(min_timestamp="2026-07-01T00:00:00Z"))
    """
    if min_timestamp is None:
        min_timestamp = pendulum.now("UTC").subtract(days=7).to_iso8601_string()

    config: RESTAPIConfig = {
        "client": {
            "base_url": base_url,
            "auth": {
                "type": "bearer",
                "token": read_token,
            },
            "headers": {
                "Accept": "application/json",
            },
            "paginator": "single_page",
        },
        "resources": [
            {
                "name": "records",
                "endpoint": {
                    "path": "v2/query",
                    "method": "POST",
                    "json": {
                        "sql": "SELECT * FROM records",
                        "min_timestamp": min_timestamp,
                        "limit": 1000,
                    },
                    "data_selector": "data",
                },
            },
        ],
    }

    yield from rest_api_resources(config)


def load_logfire() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="rest_api_logfire",
        destination="duckdb",
        dataset_name="logfire_data",
        dev_mode=True,
    )

    load_info = pipeline.run(logfire_source())
    print(load_info)  # noqa: T201


if __name__ == "__main__":
    load_logfire()
