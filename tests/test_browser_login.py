from ask_notebooklm.browser_login import has_google_auth_cookie


def test_has_google_auth_cookie_accepts_google_auth_cookie():
    cookies = [{"name": "__Secure-1PSID", "domain": ".google.com"}]

    assert has_google_auth_cookie(cookies)


def test_has_google_auth_cookie_rejects_non_google_cookie():
    cookies = [{"name": "__Secure-1PSID", "domain": ".example.com"}]

    assert not has_google_auth_cookie(cookies)
