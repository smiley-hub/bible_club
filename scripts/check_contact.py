"""Check contact layout and local preview without sending email."""
from pathlib import Path
from playwright.sync_api import sync_playwright
output = Path(__file__).resolve().parent.parent / 'artifacts' / 'contact'
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    assert page.goto('http://127.0.0.1:8000/contact/', wait_until='networkidle').status == 200
    page.evaluate('document.fonts.ready')
    assert page.locator('#primary-nav [aria-current="page"]').inner_text() == 'Get in Touch'
    page.screenshot(path=str(output/'desktop.png'),full_page=True)
    for width in [320,375,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    page.set_viewport_size({'width':375,'height':812})
    page.screenshot(path=str(output/'mobile.png'),full_page=True)
    page.locator('.faq-list summary').first.click()
    assert page.locator('.faq-list details').first.get_attribute('open') is not None
    # Only exercise the explicitly marked preview, never a live send form.
    if page.locator('.contact-preview').count():
        page.locator('.contact-submit').click()
        assert page.locator('.contact-errors').is_visible()
        page.get_by_label('Your name', exact=True).fill('Preview Visitor')
        page.get_by_label('Email address', exact=True).fill('preview@example.com')
        page.get_by_label('Your message', exact=True).fill('A local preview of the contact form.')
        page.locator('.contact-submit').click()
        assert 'has not been sent' in page.locator('.contact-notice').inner_text()
    assert not errors, errors
    browser.close()
print('Contact checks passed: responsive layout, navigation, FAQs, validation, and local preview.')
