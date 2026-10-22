"""Browser smoke checks. Run with the local Django server on port 8000."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright

output = ROOT / 'artifacts' / 'homepage'
output.mkdir(parents=True, exist_ok=True)
base_url = 'http://127.0.0.1:8000'

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    response = page.goto(base_url, wait_until='networkidle')
    assert response.status == 200
    page.evaluate('document.fonts.ready')
    assert page.evaluate("document.fonts.check('16px Lora')")
    assert page.evaluate("document.fonts.check('16px \"Source Sans 3\"')")
    assert not page.locator('.menu-toggle').is_visible()
    page.screenshot(path=str(output / 'desktop.png'), full_page=True)
    for width in [375, 320, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
    page.set_viewport_size({'width': 375, 'height': 812})
    page.locator('.menu-toggle').click()
    assert page.locator('#primary-nav').is_visible()
    page.locator('#primary-nav a[href="/contact/"]').click()
    assert not page.locator('#primary-nav').is_visible()
    page.locator('.faq-list summary').first.click()
    assert page.locator('.faq-list details').first.get_attribute('open') is not None
    page.locator('.faq-list summary').first.click()
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(400)
    page.screenshot(path=str(output / 'mobile.png'), full_page=True)

    # Isolated rendered fixture exercises real slideshow code without seeding the
    # club database or generating/editing any photographs.
    fixture = render_to_string('core/home.html', {'slides': [
        SimpleNamespace(image=SimpleNamespace(url='/static/images/book.svg'),
                        alt_text=f'Test slide {index}', caption='') for index in range(3)
    ]})
    page.route('**/__slideshow_check', lambda route: route.fulfill(body=fixture, content_type='text/html'))
    page.emulate_media(reduced_motion='reduce')
    page.goto(base_url + '/__slideshow_check', wait_until='networkidle')
    assert page.locator('[data-slide]:visible').count() == 1
    assert page.locator('[data-pause]').inner_text() == 'Play'
    page.locator('[data-next]').click()
    assert page.locator('[data-slide]:visible img').get_attribute('alt') == 'Test slide 1'
    page.locator('[data-previous]').click()
    page.locator('[data-previous]').click()
    assert page.locator('[data-slide]:visible img').get_attribute('alt') == 'Test slide 2'
    page.locator('[data-go="0"]').click()
    assert page.locator('[data-slide]:visible img').get_attribute('alt') == 'Test slide 0'
    page.locator('[data-next]').focus()
    page.keyboard.press('ArrowRight')
    assert page.locator('[data-slide]:visible img').get_attribute('alt') == 'Test slide 1'
    page.locator('[data-pause]').click()
    assert page.locator('[data-pause]').inner_text() == 'Pause'
    page.mouse.move(0, 0)
    page.wait_for_timeout(6800)
    assert page.locator('[data-slide]:visible img').get_attribute('alt') == 'Test slide 2'
    page.locator('[data-pause]').click()
    assert page.locator('[data-pause]').inner_text() == 'Play'
    page.emulate_media(reduced_motion='no-preference')
    page.reload(wait_until='networkidle')
    assert page.locator('[data-pause]').inner_text() == 'Pause'
    page.locator('[data-pause]').click()
    assert page.locator('[data-pause]').inner_text() == 'Play'
    no_js = browser.new_context(java_script_enabled=False, viewport={'width': 375, 'height': 812})
    fallback = no_js.new_page()
    fallback.goto(base_url, wait_until='networkidle')
    assert fallback.locator('#primary-nav').is_visible()
    fallback.locator('.faq-list summary').first.click()
    assert fallback.locator('.faq-list details').first.get_attribute('open') is not None
    no_js.close()
    assert not errors, errors
    browser.close()
print('Browser checks passed: fonts, five viewport widths, mobile menu, FAQ, slideshow, reduced motion, autoplay, and no JavaScript errors.')
print(f'Screenshots: {output}')
