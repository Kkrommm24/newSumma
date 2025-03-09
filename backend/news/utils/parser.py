from urllib.parse import urljoin

class NewsParser:
    @staticmethod
    def parse_baomoi(html):
        return [{"title": a.text.strip(), "url": urljoin("https://baomoi.com", a["href"])}
                for a in html]

    @staticmethod
    def parse_bbc(html):
        return [{"title": a.text.strip(), "url": urljoin("https://www.bbc.com", a["href"])}
                for a in html]

    @staticmethod
    def parse_nytimes(html):
        return [{"title": a.text.strip(), "url": urljoin("https://www.nytimes.com", a["href"])}
                for a in html]
