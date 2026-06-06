import json
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


def get_json(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
    if params:
        url = "{}?{}".format(url, urlencode(params))
    request_headers = {"User-Agent": "akimi-world-cup-radar/1.0"}
    request_headers.update(headers or {})
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ProviderError("Provider request failed: {}".format(error)) from error
