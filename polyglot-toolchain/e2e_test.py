from __future__ import annotations
import os
import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}


def main():
    headers = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"),headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=180) as client:
        assert client.get("/health").status_code == 200
        discovery = client.get("/commands")
        assert discovery.status_code == 200
        assert {item['name'] for item in discovery.json()['commands']} == {'toolchain_versions', 'toolchain_smoke'}
        print('[PASS] actual public command discovery lists both registered toolchain methods')
        response = client.post("/commands/toolchain_versions",json={})
        assert response.status_code == 200
        result = response.json()["result"]
        pins = {'go':'go1.25.14','rustc':'1.90.0','cargo':'1.90.0','java':'21.0.12.1','javac':'21.0.12.1'}
        exact = all(result.get(n) and pin in result[n] for n,pin in pins.items())
        if not exact:
            assert os.environ.get('E2E_REQUIRE_TOOLCHAIN') != '1', 'required pinned toolchains missing'
            print('[SKIP] actual compiler smoke: local exact toolchains absent')
            return 0
        result=client.post('/commands/toolchain_smoke',json={})
        assert result.status_code==200 and result.json()['result']=={'go':'GO_OK','rust':'RUST_OK','java':'JAVA_OK','cleanup_verified':True}
        print('[PASS] real installed pins and Go/Rust/Java compilation, execution and cleanup')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
