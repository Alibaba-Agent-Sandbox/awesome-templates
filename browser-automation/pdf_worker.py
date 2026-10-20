"""Trusted one-shot renderer. URL/config enters only on private file stdin."""
import json
import sys
from playwright.sync_api import sync_playwright


def main():
    data=sys.stdin.buffer.read(512*1024+1)
    if len(data)>512*1024:raise ValueError('oversize renderer input')
    value=json.loads(data)
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
        try:
            page=browser.new_page();page.set_default_timeout(value['timeout_s']*1000)
            page.goto(value['url'],wait_until='load',timeout=value['timeout_s']*1000)
            page.pdf(path=value['path'],format='A4',landscape=value['landscape'],print_background=value['print_background'])
        finally:browser.close()
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:raise SystemExit(1) from None
