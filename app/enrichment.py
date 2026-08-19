import httpx


def get_geo_from_provider_a(ip: str):
    """Primary provider: ip-api.com"""
    try:
        response = httpx.get(f"http://ip-api.com/json/{ip}", timeout=3)
        data = response.json()
        if data.get("status") == "success":
            return {"country": data.get("country"), "city": data.get("city")}
    except Exception:
        pass
    return None


def get_geo_from_provider_b(ip: str):
    """Fallback provider: ipapi.co"""
    try:
        response = httpx.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        data = response.json()
        if not data.get("error"):
            return {"country": data.get("country_name"), "city": data.get("city")}
    except Exception:
        pass
    return None


def enrich_ip(ip: str):
    """Try provider A first, then provider B. If both fail, return empty geo data."""
    if ip in ("127.0.0.1", "testclient", "localhost"):
        # local testing ke waqt fake data dikhao, real IP nahi hoti
        return {"country": "Pakistan", "city": "Islamabad"}

    result = get_geo_from_provider_a(ip)
    if result:
        return result

    result = get_geo_from_provider_b(ip)
    if result:
        return result

    return {"country": None, "city": None}