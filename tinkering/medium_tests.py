import requests
from bs4 import BeautifulSoup

url = 'https://medium.com/@dacoker/bitcoin-what-are-you-waiting-for-6a9b62c45d7a'

# Header NovelLive
header = {'authority': 'medium.com',
          'method': 'GET',
          'path': '/@dacoker/bitcoin-what-are-you-waiting-for-6a9b62c45d7a',
          'scheme': 'https',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'max-age=0',
          'Cookie': 'g_state={"i_p":1708488905959,"i_l":1}; nonce=88qQqb0p; sid=1:ypXx3e3XldyNeXBNX81GoP8GGfuEWgmgWl+AFit/nrdp1+oMYSLl6Cp/L0XqxPFC; uid=23496c5559c4; _ga=GA1.1.783535672.1708481698; _cfuvid=q3hZnIl2c83YFBU_WvC7mzHue17CRUrAKR0zEQ5Gmak-1721170330909-0.0.1.1-604800000; xsrf=022cd39b3a2b; _ga_7JY7T788PK=GS1.1.1721344896.4.1.1721344953.0.0.0; _dd_s=rum=0&expire=1721345901543',
          'Referer': 'https://www.google.com/',
          'Sec-Ch-Ua': '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
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


with open('teste.txt', 'w', encoding='utf-8') as file:
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find_all('div', class_='ch bg eu ev ew ex')

print(content)
# Problemas com o paywall