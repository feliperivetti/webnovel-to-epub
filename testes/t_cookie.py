import requests

# url = 'https://www.royalroad.com/fiction/36735/the-perfect-run/chapter/569225/1-quicksave'
url = 'https://ranobes.top/novels/244294-the-beginning-after-the-end-v812312.html'


response = requests.get(url)

print(response.cookies.get_dict())