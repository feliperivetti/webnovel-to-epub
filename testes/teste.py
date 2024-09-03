import requests
from bs4 import BeautifulSoup


# Header Ranobes
"""header = {'authority': 'ranobes.top',
          'method': 'GET',
          'path': '/novels/244294-the-beginning-after-the-end-v812312.html',
          'scheme': 'https',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'max-age=0',
          'Cookie': 'PHPSESSID=mkgta8hivb03fjn90ljnej61ok; _ym_uid=1720809034168106225; _ym_d=1720809034; _pubcid=9d4d3dbb-1ca8-4d38-952c-b10f99088c74; _pubcid_cst=zix7LPQsHA%3D%3D; viewed_ids=244294,1206553,1206532; read_mark=%7B%221206532%22%3A2588516%2C%221206553%22%3A2586060%2C%22244294%22%3A364930%7D; viewed_chapter_ids=364930,2588516,2586060,2586605; cf_clearance=JlbKUPg0QRypp26Ckif9VL2ymG991VIjvf9Ou5BFZsQ-1722886616-1.0.1.1-fG4Tfh_WFxFIg5VPSdUN3C1bH_ccoK1epV3oJR08mJwv0GL9KvD0zAAfMX1xpIH4DVAsBeftYylceYXeaOd3nA; _ym_isad=2',
          'Referer': 'https://ranobes.top/the-beginning-after-the-end-v812312-244294/364930.html',
          'Sec-Ch-Ua': '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'same-origin',
          'Sec-Fetch-User': '?1',
          'Upgrade-Insecure-Requests': '1',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
          }"""

# Header NovelLive
"""header = {'authority': 'novellive.org',
          'method': 'GET',
          'path': '/book/the-beginning-after-the-end/chapter-1',
          'scheme': 'https',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'max-age=0',
          'Cookie': '_csrf=13Nbd3GjQoxCVh2D_JgSir2H; _ga=GA1.1.1563173162.1721339168; truvid_protected={"val":"c","level":2,"geo":"BR","timestamp":1721344872}; cto_bundle=-QJvbF9KS0J0dVpVNXZ5Snd3ZVRjaTVjazRNOE5XS3dwT00xQkp1NlpOcW1rJTJGQnNITTFoZjdFYk05QTNmUUhKRDNlMlRZUnQzcVN4QmFteGEweFAyOHk3Vmp1cDlqUXZvc1NnTG1lQXdQbjRDYzhwdk92V2IxWVBmM05NTjhwUHIxSjhudEhCaExDVGl1cHNrdG5kS0xNeVdNZyUzRCUzRA; cto_bidid=jkwbY192YUxnU3NHZ09EcEUlMkJrSjl0SVBTZ3p6UUJKbmUlMkZLeWlOYnFMaTU5N0FpZVN5ZmdMTkpETiUyQms0OEVpaCUyRk85VHd4UlVIbE1mR0N6eHUyT2lZdzYxdkdXYlVFS3F1Q2kxZ29pM1BWY1A0NUkwJTNE; cf_clearance=zYnjzstkyaE6sy3kZyqi_PIc4N2scihQYEfZyJOtRno-1722990097-1.0.1.1-7FcyzrFNJS8UT_Oh0BeawzgDCZF1gjhDcnBRXiV6CaiM74k8shJBrdqIezeRarpD_1Ls50dHhEgMW4JlGF7e1A; _ga_GFW242RQ9C=GS1.1.1722990088.4.1.1722990098.0.0.0',
          'Referer': 'https://novellive.org/book/the-beginning-after-the-end/chapter-1?__cf_chl_tk=YYQYz5_5PdEZbVN9OaQVrErzpbIJ2zUvIH8vh97FNGQ-1721339158-0.0.1.1-4521',
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
          }"""

# Header NovelBin
header = {'authority': 'novelbin.com',
          'method': 'GET',
          'path': '/b/shadow-slave',
          'scheme': 'https',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          'Cache-Control': 'max-age=0',
          'Cookie': '_csrf=D99O5jOvKWko_ERGqbd73-wu; _ga=GA1.1.1218856484.1723000827; _gaClientId=1218856484.1723000827; cf_clearance=GOs0R1hauwDa3PmbyPIKH8QpybrOm5ZI5xS4mQX5NEM-1723040575-1.0.1.1-IBCP02Mi3xmXGMABpXmzCZnNwqruvwD9qpW2ZdLAlf8iYGMGSQtVZhVEfgVmQjnwQiIPpMoKThKXyWPYQP5Rpg; _ga_15YCML7VSC=GS1.1.1723042672.3.0.1723042672.0.0.',
          'Sec-Ch-Ua': '"Opera GX";v="109", "Not:A-Brand";v="8", "Chromium";v="123"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none',
          'Sec-Fetch-User': '?1',
          'Upgrade-Insecure-Requests': '1',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
          }


# url = 'https://ranobes.top/novels/244294-the-beginning-after-the-end-v812312.html'
# url = 'https://novellive.org/book/the-beginning-after-the-end/chapter-1'
# url = 'https://novellive.org/book/the-beginning-after-the-end/'

# url = 'https://www.lightnovelworld.com/novel/genetic-ascension'
# url = 'https://novelbin.com/b/shadow-slave'
# url = 'https://novelfull.com/shadow-slave.html'
# url = 'https://novelfull.net/shadow-slave.html'
# url = 'https://novelbuddy.net/novel/shadow-slave'
url = 'https://pandanovel.co/panda-novel/shadow-slave'



# response = requests.get(url)
# print(f"Código de Status da Requisição: {response.status_code}")
# print(response.encoding)
# print(response.text)
# print(r.request.headers)

chapter_list = []
for i in range(18):
    url = 'https://pandanovel.co/panda-novel/shadow-slave' + f'/chapters?page={i+1}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    teste = soup.find('ul', class_='chapter-list')
    lista = teste.find_all('a')
    for item in lista:
        chapter_list.append(item['href'])

print(chapter_list)

    


# with open('teste66.bin', 'wb') as f:
#     noop = f.write(response.content)


# teste = response.content
# a = teste.decode('utf-8') #iso-8859-1
# print(a)
# print(url)

