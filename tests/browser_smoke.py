"""Optional synthetic UI smoke. Run against local uvicorn; no live Gnani calls."""
from pathlib import Path
from playwright.sync_api import sync_playwright

if __name__=='__main__':
    Path('work').mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8000')
        page.locator('#sessionLabel').filter(has_text='-').wait_for()
        page.get_by_role('button',name='New session').click()
        page.locator('#transcript').fill('No water since yesterday; streetlight not working for three days')
        page.get_by_role('button',name='Review my intent').click()
        page.wait_for_function("document.querySelectorAll('.issue').length === 2")
        assert page.locator('[data-action="confirm"]').count()==2
        assert page.locator('[data-action="confirm"]').first.is_disabled()
        page.locator('#target').select_option(index=1)
        page.locator('#transcript').fill('at house 24')
        page.get_by_role('button',name='Review my intent').click()
        page.get_by_text('House 24',exact=True).wait_for()
        page.locator('[data-action="confirm"]').first.click()
        page.locator('.status',has_text='confirmed').wait_for()
        sid=page.locator('#resumeId').input_value()
        page.reload();page.locator('.status',has_text='confirmed').wait_for()
        assert page.locator('#resumeId').input_value()==sid
        first=page.locator('.issue').first
        first.get_by_text('Review or correct fields manually',exact=True).click()
        first.locator('input[name="location"]').fill('24, Maple Avenue, Bengaluru')
        first.get_by_role('button',name='Save reviewed fields').click()
        page.get_by_text('24, Maple Avenue, Bengaluru',exact=True).wait_for()
        assert page.locator('.status',has_text='confirmed').count()==0
        page.locator('[data-action="confirm"]').first.click()
        page.locator('.status',has_text='confirmed').wait_for()
        page.screenshot(path='work/desktop.png',full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path='work/mobile.png',full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        print('PASS: multi-issue; missing-field gate; scoped clarification; explicit confirmation; reload continuity; manual edit revocation; mobile overflow; no JS errors. No live STT calls.')
        browser.close()
