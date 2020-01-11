import os
import uuid
import urllib.parse
import logging
import aiohttp
import async_timeout
import asyncio
import collections
from urllib.parse import urlparse

from homeassistant.helpers import template
from homeassistant.components.http import HomeAssistantView

from homeassistant.components.weblink import Link
from aiohttp import web
from aiohttp.hdrs import CACHE_CONTROL, CONTENT_TYPE
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)

_LOGGER = logging.getLogger(__name__)

CACHE_LOCK = "lock"
CACHE_IMAGES = "images"
CACHE_MAXSIZE = "maxsize"
CACHE_CONTENT = "content"
ENTITY_IMAGE_CACHE = {CACHE_IMAGES: collections.OrderedDict(), CACHE_MAXSIZE: 16}

DOMAIN = 'ha_camera'
VERSION = '1.0'
URL = '/'+DOMAIN+'-api-'+ str(uuid.uuid4())
ROOT_PATH = URL + '/' + VERSION

def async_setup(hass, config):
    # 显示插件信息
    _LOGGER.info('''
-------------------------------------------------------------------
    监控摄像头【作者QQ：635147515】
    
    版本：''' + VERSION + '''  

    安全URL：''' + URL + '''      
        
    项目地址：https://github.com/shaonianzhentan/ha_camera
-------------------------------------------------------------------''')
    cfg  = config[DOMAIN]
    # 注册静态目录
    local = hass.config.path('custom_components/'+DOMAIN+'/local')
    if os.path.isdir(local):
        hass.http.register_static_path(ROOT_PATH, local, False)

    # 摄像头IP
    _ip = cfg.get('ip', '')
    _user = cfg.get('user', '')
    _password = cfg.get('password', '')
    _snapshot = cfg.get('snapshot', '')

    hass.data[URL] = HaCamera(hass, _ip,_user,_password,_snapshot)

    hass.http.register_view(HassGateView)
    
    Link(hass, "摄像监控", URL, "mdi:camcorder-box")
    # 加载自定义卡片
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/ha-camera-panel.js')
    return True

class HassGateView(HomeAssistantView):

    url = URL
    name = DOMAIN
    requires_auth = False
    
    async def get(self, request):
        # 这里进行重定向
        hass = request.app["hass"]
        camera = hass.data[URL]        
        query = request.query
        
        if 'url' in query:
            _url = query['url']
            data, content_type = await camera.async_fetch_image(_url)
            return web.Response(body=data, content_type=content_type, headers={})
            
        #headers = {CACHE_CONTROL: "max-age=3600"}
        return self.json({})
        
class HaCamera:

    def __init__(self, hass, ip, user, password, snapshot):
        self.ip = ip
        self.user = user
        self.password = password
        self.snapshot = snapshot
        self.hass = hass
            
    async def async_fetch_image(self, url):
        """Fetch image.
        Images are cached in memory (the images are typically 10-100kB in size).
        """
        hass = self.hass
        cache_images = ENTITY_IMAGE_CACHE[CACHE_IMAGES]
        cache_maxsize = ENTITY_IMAGE_CACHE[CACHE_MAXSIZE]

        if urlparse(url).hostname is None:
            url = hass.config.api.base_url + url

        if url not in cache_images:
            cache_images[url] = {CACHE_LOCK: asyncio.Lock()}

        async with cache_images[url][CACHE_LOCK]:
            if CACHE_CONTENT in cache_images[url]:
                return cache_images[url][CACHE_CONTENT]

            content, content_type = (None, None)
            websession = async_get_clientsession(hass)
            try:
                with async_timeout.timeout(10):
                    response = await websession.get(url)

                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get(CONTENT_TYPE)
                        if content_type:
                            content_type = content_type.split(";")[0]
                        cache_images[url][CACHE_CONTENT] = content, content_type

            except asyncio.TimeoutError:
                pass

            while len(cache_images) > cache_maxsize:
                cache_images.popitem(last=False)

            return content, content_type
