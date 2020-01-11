import os
import uuid
import urllib.parse
import logging
import aiohttp
import async_timeout

from homeassistant.helpers import template
from homeassistant.components.http import HomeAssistantView
from aiohttp import web
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ha_camera'
VERSION = '1.0'
URL = '/'+DOMAIN+'-api-'+ str(uuid.uuid4())
ROOT_PATH = URL + '/' + VERSION

def setup(hass, config):
    # 显示插件信息
    _LOGGER.info('''
-------------------------------------------------------------------
    监控摄像头【作者QQ：635147515】
    
    版本：''' + VERSION + '''    
        
    项目地址：https://github.com/shaonianzhentan/ha_camera
-------------------------------------------------------------------''')
    cfg  = config[DOMAIN]
    # 注册静态目录
    local = hass.config.path('custom_components/'+DOMAIN+'/local')
    if os.path.isdir(local):
        hass.http.register_static_path(ROOT_PATH, local, False)

    # 摄像头IP
    _ip = cfg.get('ip')
    _user = cfg.get('user')
    _password = cfg.get('password')
    _snapshot = cfg.get('snapshot')

    hass.data[DOMAIN] = HaCamera(hass, _ip,_user,_password,_snapshot)

    hass.http.register_view(HassGateView)
    return True

class HassGateView(HomeAssistantView):

    url = URL
    name = DOMAIN
    requires_auth = False
    
    async def get(self, request):
        # 这里进行重定向
        hass = request.app["hass"]
        camera = hass.data[DOMAIN]
        return await camera.async_camera_image()
        
class HaCamera:

    def __init__(self, hass, ip, user, password, snapshot):
        self.ip = ip
        self.user = user
        self.password = password
        self._still_image_url = snapshot
        self._verify_ssl = False
        self.hass = hass
    
    async def async_camera_image(self):
        """Return a still image response from the camera."""

        websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        try:
            with async_timeout.timeout(10):
                response = await websession.get(self._still_image_url, auth=self._auth)

                image = await response.read()
                return image

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout getting camera image")

        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting new camera image: %s", err)
