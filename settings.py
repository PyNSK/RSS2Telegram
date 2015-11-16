RSS_URL = 'http://feed.exileed.com/vk/feed/pynsk'
TGM_BOT_ACCESS_TOKEN = ''
TGM_CHANNEL = '@pynsk'

try:
    from local_settings import *
except ImportError as e:
    print(e)
