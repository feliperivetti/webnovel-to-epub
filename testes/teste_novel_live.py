import requests
from bs4 import BeautifulSoup

url = 'https://novellive.org/book/the-beginning-after-the-end/'

# Header NovelLive
header = {'authority': 'novellive.org',
          'method': 'GET',
          'path': '/book/the-beginning-after-the-end/',
          'scheme': 'https',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'max-age=0',
          'Cookie': '_csrf=13Nbd3GjQoxCVh2D_JgSir2H; _ga=GA1.1.1563173162.1721339168; truvid_protected={"val":"c","level":2,"geo":"BR","timestamp":1721344872}; cto_bundle=-QJvbF9KS0J0dVpVNXZ5Snd3ZVRjaTVjazRNOE5XS3dwT00xQkp1NlpOcW1rJTJGQnNITTFoZjdFYk05QTNmUUhKRDNlMlRZUnQzcVN4QmFteGEweFAyOHk3Vmp1cDlqUXZvc1NnTG1lQXdQbjRDYzhwdk92V2IxWVBmM05NTjhwUHIxSjhudEhCaExDVGl1cHNrdG5kS0xNeVdNZyUzRCUzRA; cto_bidid=jkwbY192YUxnU3NHZ09EcEUlMkJrSjl0SVBTZ3p6UUJKbmUlMkZLeWlOYnFMaTU5N0FpZVN5ZmdMTkpETiUyQms0OEVpaCUyRk85VHd4UlVIbE1mR0N6eHUyT2lZdzYxdkdXYlVFS3F1Q2kxZ29pM1BWY1A0NUkwJTNE; _ga_GFW242RQ9C=GS1.1.1722886443.3.1.1722886566.0.0.0; cf_clearance=niEvTXUIz7iCNul_ORAQ0pMyXQ7PVh0aQ4eRNYZm0e4-1722886567-1.0.1.1-QI0bToFzYLOPtTbaF9BwpsWvFeuTQzFARJjQ6qwn7KQ1xrjOwZY9lgBqGk48hpYLjEITZtd69gXxvWgUJczChg',
          'Referer': 'https://novellive.org/book/the-beginning-after-the-end/?__cf_chl_tk=uCPlfcHADuu5LefTCZMQ2Sf1ByMmVV2cQTJgM4fLP8I-1722886429-0.0.1.1-5438',
          'Sec-Ch-Ua': '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
          'Sec-Ch-Ua-Arch': '"x86"',
          'Sec-Ch-Ua-Bitness': '"64"',
          'Sec-Ch-Ua-Full-Version': '"109.0.5097.142"',
          'Sec-Ch-Ua-Full-Version-List': '"Opera GX";v="109.0.5097.142", "Not:A-Brand";v="8.0.0.0", "Chromium";v="123.0.6312.124"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Model': '""',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'same-origin',
          'Sec-Fetch-User': '?1',
          'Upgrade-Insecure-Requests': '1',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
          }

response = requests.get(url, headers=header)
print(response.status_code)
print(response.encoding)
# print(response.text)
print(response.content)

