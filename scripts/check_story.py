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
    assert not page.locator('[data-history-road]').is_visible()
    page.locator('[data-open-journey]').focus()
    page.keyboard.press('Enter')
    assert page.locator('[data-open-journey]').get_attribute('aria-expanded') == 'true'
    assert page.locator('[data-chapter]:visible').count() == 11
    page.locator('[data-open-journey]').click()
    page.wait_for_timeout(700)
    assert not page.locator('[data-history-road]').is_visible()
    assert page.locator('[data-open-journey]').get_attribute('aria-expanded') == 'false'
    assert page.locator('[data-open-journey]').evaluate('(el) => el === document.activeElement')
    page.keyboard.press('Enter')
    assert page.locator('[data-chapter]:visible').count() == 11
    page.locator('[data-chapter-select]').select_option('chapter-11')
    page.wait_for_timeout(1200)
    assert page.locator('#chapter-11').evaluate('(el) => el === document.activeElement')
    assert page.locator('#chapter-11').evaluate('(el) => el.getBoundingClientRect().top < innerHeight')
    assert page.locator('[data-timeline]').evaluate('(el) => el.scrollLeft > 0')
    assert page.locator('[data-timeline-next]').is_disabled()
    page.locator('[data-timeline]').focus()
    page.keyboard.press('Home')
    page.wait_for_timeout(1000)
    assert page.locator('[data-timeline-previous]').is_disabled()
    page.locator('[data-timeline-next]').click()
    page.wait_for_timeout(1000)
    assert page.locator('[data-timeline]').evaluate('(el) => el.scrollLeft > 0')
    for width in [320, 375, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Open road overflow at {width}'
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('[data-history-road]').evaluate('(el) => getComputedStyle(el).animationName') == 'none'
    page.locator('[data-chapter-select]').select_option('chapter-1')
    page.screenshot(path=str(output / 'road-desktop.png'), full_page=True)
    page.set_viewport_size({'width':375,'height':812})
    page.screenshot(path=str(output / 'road-mobile.png'), full_page=True)

    page.locator('[data-open-journey]').click()
    assert not page.locator('[data-history-road]').is_visible()
    page.locator('[data-open-journey]').click()
    assert page.locator('[data-chapter]:visible').count() == 11

    page.unroute('**/__story_check')
    page.route('**/__story_check', lambda route: route.fulfill(body=fixture(1), content_type='text/html'))
    page.goto(base + '/__story_check', wait_until='networkidle')
    page.locator('[data-open-journey]').click()
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
print('Story checks passed: responsive layout, navigation, wheel opening, keyboard controls, horizontal scrolling, long history, one/zero chapters, reduced motion, no-JavaScript fallback.')
print(f'Screenshots: {output}')
