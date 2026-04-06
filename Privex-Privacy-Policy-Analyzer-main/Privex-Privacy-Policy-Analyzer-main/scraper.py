import requests
from bs4 import BeautifulSoup

def get_policy_text(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        res = requests.get(url, headers=headers, timeout=15)

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.extract()

        text = soup.get_text(separator=" ")
        text = " ".join(text.split())

        return text

    except Exception as e:
        print("Error:", e)
        return ""
