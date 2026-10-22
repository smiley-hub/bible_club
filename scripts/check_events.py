"""Browser checks for the Events pages; requires the local Django server."""
from pathlib import Path
from playwright.sync_api import sync_playwright

output = Path(__file__).resolve().parent.parent / 'artifacts' / 'events'
output.mkdir(parents=True, exist_ok=True)
base = 'http://127.0.0.1:8000'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width':1440, 'height':1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    assert page.goto(base + '/events/', wait_until='networkidle').status == 200
    page.evaluate('document.fonts.ready')
    assert page.locator('#primary-nav [aria-current="page"]').inner_text() == 'Events'
    page.screenshot(path=str(output / 'desktop.png'), full_page=True)
    detail_links = page.locator('.event-preview-copy h3 a').evaluate_all('(els) => els.map(el => el.href)')
    album_links = page.locator('.memory-copy h3 a').evaluate_all('(els) => els.map(el => el.href)')
    for width in [320, 375, 768, 1024, 1440]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow: {width}'
    page.locator('.event-filters a').filter(has_text='Outdoors').click()
    assert page.locator('.event-filters [aria-current]').inner_text() == 'Outdoors'
    page.locator('.event-filters a').filter(has_text='All memories').click()
    page.set_viewport_size({'width':375,'height':812})
    page.screenshot(path=str(output / 'mobile.png'), full_page=True)
    for url in detail_links + album_links:
        assert page.goto(url, wait_until='networkidle').status == 200
        for width in [320, 768, 1440]:
            page.set_viewport_size({'width':width,'height':900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow: {url}, {width}'
        assert page.locator('h1').inner_text()
        if '/photos/' in url:
            for href in page.locator('.event-gallery figure a').evaluate_all('(els) => els.map(el => el.href)'):
                assert page.request.get(href).status == 200
    if detail_links:
        page.goto(detail_links[0], wait_until='networkidle')
        page.screenshot(path=str(output / 'detail.png'), full_page=True)
    if album_links:
        page.goto(album_links[0], wait_until='networkidle')
        page.screenshot(path=str(output / 'album.png'), full_page=True)
    assert not errors, errors
    browser.close()
print('Events browser checks passed: navigation, filters, responsive layouts, details, albums, and photo URLs.')
print(f'Screenshots: {output}')
