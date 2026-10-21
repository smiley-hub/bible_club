"""Check Our Story in the installed Edge browser, with Django on port 8000."""
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

output = ROOT / 'artifacts' / 'story'
output.mkdir(parents=True, exist_ok=True)
base = 'http://127.0.0.1:8000'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    assert page.goto(base + '/our-story/', wait_until='networkidle').status == 200
    page.evaluate('document.fonts.ready')
    assert page.locator('#primary-nav a[aria-current="page"]').inner_text() == 'Our Story'
    page.screenshot(path=str(output / 'desktop.png'), full_page=True)
    for width in [320, 375, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
    page.set_viewport_size({'width': 375, 'height': 812})
    page.screenshot(path=str(output / 'mobile.png'), full_page=True)

    def fixture(count):
        return render_to_string('core/our_story.html', {'milestones': [
            SimpleNamespace(pk=i+1, year=2000+i, title=f'Chapter {i+1}', story=f'Story {i+1}', image=None)
            for i in range(count)
        ]})

    # Fixture tests leave all saved club content untouched.
    page.route('**/__story_check', lambda route: route.fulfill(body=fixture(11), content_type='text/html'))
    page.goto(base + '/__story_check', wait_until='networkidle')
    assert page.locator('[data-chapter]:visible').count() == 1
    assert page.locator('[data-history-previous]').is_disabled()
    page.locator('[data-history-next]').click()
    assert page.locator('[data-chapter]:visible h2').inner_text() == 'Chapter 2'
    page.locator('[data-chapter-button="2"]').click()
    assert page.locator('[data-chapter]:visible h2').inner_text() == 'Chapter 3'
    page.keyboard.press('End')
    assert page.locator('[data-chapter]:visible h2').inner_text() == 'Chapter 11'
    assert page.locator('[data-history-next]').is_disabled()
    assert page.locator('[data-chapter-button]:visible').count() == 3
    page.keyboard.press('Home')
    assert page.locator('[data-chapter]:visible h2').inner_text() == 'Chapter 1'
    page.locator('[data-chapter-select]').select_option('8')
    assert page.locator('[data-chapter]:visible h2').inner_text() == 'Chapter 9'
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('[data-wheel-orbit]').evaluate('(el) => getComputedStyle(el).transitionDuration') == '0s'

    page.unroute('**/__story_check')
    page.route('**/__story_check', lambda route: route.fulfill(body=fixture(1), content_type='text/html'))
    page.goto(base + '/__story_check', wait_until='networkidle')
    assert page.locator('[data-history-next]').is_disabled()
    assert page.locator('[data-history-previous]').is_disabled()
    assert page.locator('[data-chapter]:visible').count() == 1
    page.unroute('**/__story_check')
    page.route('**/__story_check', lambda route: route.fulfill(body=fixture(0), content_type='text/html'))
    page.goto(base + '/__story_check', wait_until='networkidle')
    assert page.locator('.story-awaiting').is_visible()

    context = browser.new_context(java_script_enabled=False)
    fallback = context.new_page()
    fallback.route('**/__story_check', lambda route: route.fulfill(body=fixture(3), content_type='text/html'))
    fallback.goto(base + '/__story_check', wait_until='networkidle')
    assert fallback.locator('[data-chapter]:visible').count() == 3
    assert not fallback.locator('[data-journey-nav]').is_visible()
    assert not errors, errors
    browser.close()
print('Story checks passed: responsive layout, navigation, wheel selection, keyboard controls, long history, one/zero chapters, reduced motion, no-JavaScript fallback.')
print(f'Screenshots: {output}')
