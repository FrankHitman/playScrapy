#!/usr/bin/env python3
"""
NHK HLS音频下载器
从M3U8播放列表下载加密的AAC音频片段并合并
https://news.web.nhk/news/easy/ne2025101017047/ne2025101017047.html

"""

import os
import re
import requests
import tempfile
from urllib.parse import urljoin
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import subprocess
from urllib.parse import urlparse, parse_qs, urlunparse, quote

class NHKHLSDownloader:
    def __init__(self, m3u8_content, cookies_string, base_url=None):
        """
        初始化下载器
        
        Args:
            m3u8_content: M3U8播放列表内容
            cookies_string: Cookie字符串
            base_url: 基础URL，用于解析相对路径
        """
        self.m3u8_content = m3u8_content
        self.cookies = self._parse_cookies(cookies_string)
        self.base_url = base_url
        self.segments = []
        self.key_uri = None
        self.key_data = None
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://news.web.nhk/',
            'DNT': '1',
            'Sec-Ch-Ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }


        
    def _parse_cookies(self, cookie_string):
        """解析cookie字符串为字典格式"""
        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        return cookies
    
    def _parse_m3u8(self):
        """解析M3U8播放列表"""
        lines = self.m3u8_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 解析加密密钥
            if line.startswith('#EXT-X-KEY:'):
                # 提取URI
                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    self.key_uri = uri_match.group(1)
                    print(f"找到加密密钥URI: {self.key_uri}")
            
            # 解析音频片段
            elif line.startswith('index_') and '.aac' in line:
                self.segments.append(line)
                print(f"找到音频片段: {line}")
        
        print(f"总共找到 {len(self.segments)} 个音频片段")
    
    def _download_key(self):
        """下载AES解密密钥"""
        if not self.key_uri:
            print("没有找到加密密钥URI")
            return False
            
        try:
            print(f"正在下载密钥: {self.key_uri}")
            # 密钥URL已经包含了必要的参数，直接使用
            response = requests.get(self.key_uri, headers=self.headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            self.key_data = response.content
            print(f"密钥下载成功，长度: {len(self.key_data)} 字节")
            return True
        except Exception as e:
            print(f"密钥下载失败: {e}")
            return False
    
    def build_media_url(self, key_url: str, segment_url: str) -> str:
        key_parts = urlparse(key_url)
        hdntl_value = parse_qs(key_parts.query)["hdntl"][0]  # raises if missing

        base_dir, _, _ = key_parts.path.rpartition("/")
        media_parts = urlparse(segment_url)
        media_path = media_parts.path.lstrip("/")

        hdntl_segment = f"hdntl={quote(hdntl_value, safe='~=*')}"
        new_path = "/".join([base_dir, hdntl_segment, media_path])

        return urlunparse((
            key_parts.scheme,
            key_parts.netloc,
            "/" + new_path.lstrip("/"),
            "",
            media_parts.query,
            ""
        ))
    
    def _download_segment(self, segment_name, output_dir):
        """下载单个音频片段"""
        # 构建完整URL
        # request with required payload parameters to avoid 403 error,
        # the parameters are already in the m3u8 file
        segment_url = self.build_media_url(self.key_uri, segment_name)
        print(f"构建的完整URL: {segment_url}")
        try:
            print(f"正在下载片段: {segment_name}")
            response = requests.get(segment_url, headers=self.headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            
            # 保存加密的音频数据
            encrypted_data = response.content
            segment_path = os.path.join(output_dir, f"{segment_name}.encrypted")
            
            with open(segment_path, 'wb') as f:
                f.write(encrypted_data)
            
            # 解密音频数据
            if self.key_data:
                decrypted_data = self._decrypt_segment(encrypted_data)
                decrypted_path = os.path.join(output_dir, f"{segment_name}.decrypted")
                
                with open(decrypted_path, 'wb') as f:
                    f.write(decrypted_data)
                
                print(f"片段解密成功: {segment_name}")
                return decrypted_path
            else:
                print(f"片段下载成功但未解密: {segment_name}")
                return segment_path
                
        except Exception as e:
            print(f"片段下载失败 {segment_name}: {e}")
            return None
    
    def _decrypt_segment(self, encrypted_data):
        """使用AES-128解密音频片段"""
        try:
            # 创建AES解密器
            cipher = AES.new(self.key_data, AES.MODE_CBC)
            
            # 解密数据
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # 去除填充
            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                # 如果去填充失败，可能数据没有填充
                pass
            
            return decrypted_data
            
        except Exception as e:
            print(f"解密失败: {e}")
            return encrypted_data
    
    def _merge_audio_segments(self, segment_files, output_path):
        """合并音频片段"""
        try:
            # 使用ffmpeg合并音频片段
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for segment_file in segment_files:
                    if segment_file and os.path.exists(segment_file):
                        f.write(f"file '{os.path.abspath(segment_file)}'\n")
                concat_file = f.name
            
            # 执行ffmpeg命令
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0', 
                '-i', concat_file, '-c', 'copy', 
                '-y', output_path
            ]
            
            print(f"正在合并音频片段到: {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 清理临时文件
            os.unlink(concat_file)
            
            if result.returncode == 0:
                print("音频合并成功!")
                return True
            else:
                print(f"音频合并失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"合并音频时出错: {e}")
            return False
    
    def download(self, output_path="output.m4a"):
        """下载并合并所有音频片段"""
        print("开始解析M3U8播放列表...")
        self._parse_m3u8()
        
        if not self.segments:
            print("没有找到音频片段")
            return False
        
        # 下载密钥
        if self.key_uri:
            if not self._download_key():
                print("密钥下载失败，将尝试下载未解密的片段")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"使用临时目录: {temp_dir}")
            
            # 下载所有片段
            segment_files = []
            for i, segment in enumerate(self.segments, 1):
                print(f"下载进度: {i}/{len(self.segments)}")
                segment_file = self._download_segment(segment, temp_dir)
                segment_files.append(segment_file)
            
            # 合并音频片段
            if segment_files:
                return self._merge_audio_segments(segment_files, output_path)
            else:
                print("没有成功下载任何片段")
                return False

def main():
    # M3U8播放列表内容
    m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:7
#EXT-X-MEDIA-SEQUENCE:1
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-KEY:METHOD=AES-128,URI="https://media.vd.st.nhk/news/easy_audio/ne2025101017047_4IoalMQ7I5LORUIVdT34ExOCPsoXNKeSeEYMwuSy/serve.key?hdntl=exp=1760267440~acl=/*~data=hdntl~hmac=d4c8373db47aa78e836a0364b328906a149cfef8477ab7af22754ac74c007aed&aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_media_format_type=hls"
#EXTINF:6.016,
index_64k_00001.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00002.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=2&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00003.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=3&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00004.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=4&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00005.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=5&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00006.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=6&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00007.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=7&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00008.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=8&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00009.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=9&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00010.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=10&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:1.836,
index_64k_00011.aac?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_msn=11&aka_hls_version=3&aka_media_format_type=hls
#EXT-X-ENDLIST"""

    m3u8_content2="""
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:7
#EXT-X-MEDIA-SEQUENCE:1
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-KEY:METHOD=AES-128,URI="https://media.vd.st.nhk/news/easy_audio/ne2025101012062_veGbQ9D7MZGDNIUGzqW97D35WRBjpUSYCUrDy9Sf/serve.key?hdntl=exp=1760413473~acl=/*~data=hdntl~hmac=306b8ecbaedcaf7ae5160b935f5973704be9a16ab9a1a5e8a8363e2e827729ec&aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_media_format_type=hls"
#EXTINF:6.016,
index_64k_00001.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00002.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=2&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00003.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=3&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00004.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=4&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00005.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=5&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00006.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=6&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00007.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=7&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00008.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=8&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00009.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=9&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:1.280,
index_64k_00010.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=10&aka_hls_version=3&aka_media_format_type=hls
#EXT-X-ENDLIST

"""
    # Cookie字符串
    cookies_string = """emergency-mode=0; efm={"sd":"2025-10-09T12:36:29.877Z","ed":"2025-10-16T12:36:29.877Z"}; consentToUse={"status":"optedin","entity":"household","area":{"areaId":"130","jisx0402":"13113","postal":"1508001","pref":"13"}}; bff-rt-authz=cjAyOnJXR2x0S0lxZ0hHZHptZGxqTlNYVCtmQ2ZyZ2gzT0NpNEpUTlhFTDVZMEtNZU1mV2RnRzVZQUQ5R1pJcHdFRU1iZForS040OHcwV0NBT0U9OnZrbHRIOG1PNE1sa1pOM1Q=; exp_z_rt=1762605391; authz_type=r-alaz; area_permanent=130; nhkApVolume=0.7; ak_bmsc=BB86E9E0ADCE452B5F6FEE777A6D175A~000000000000000000000000000000~YAAQBX8mFy2LwcyZAQAAoXfK0h3te3gq1qUD4drncdxgx+sNVLGr8KHoDNieW8EDcZCuC3ODYZYZicqwhmJW4UA70gXgJAftl95NckPn3ULfyRVgLnUMwQpHiwpIVHPCcdHur5R7+gCXeXyu+5dEXnm/+ssap7to9mFG7v5Bx40qcgtBnQkKgRFdRZTEWi3o7JB3Cf37SchqnSQPto8UD5XTADd5XVofFT6D4SbLXY/3HlBhSBTvSVUQF6bSfqyVCbJEd6TOH0jqDdkR2bEzFo9MIZIvcD3/WbCPEpYTxFc2NWCPenLv71NgSbiT85Q58QRyA9kpRFRMtgIcGgFH+ZuJuccs30eEO7tcTtjpxJzNVNLlggHKC53ZLF8XB4vShyF1hGn3c+5xJKP1Tv1Ke8U2SFq571u79Q==; z_at=eyJhbGciOiJFUzI1NiIsInR5cCI6ImF0K2p3dCIsImtpZCI6ImtpZC1hdXRoei1hYzEtcHJkLTAxIn0.eyJzdWIiOiJjOTcwOWZiMi0zYjE5LTQxYjItYjg2My03MzczY2QxYzEzYjUiLCJpc3MiOiJodHRwczovL3IuYXV0aHouYWMxLm5oayIsImFjdGl2YXRlZEJ5Ijoic2VsZi1hY3RpdmF0ZWQiLCJjbGllbnRfaWQiOiIxMzExNjg5NDQ0MCIsImxpY2Vuc2VUeXBlIjoiMiIsInByb2ZpbGVUeXBlIjoiYW5vbnltb3VzIiwiZ3JhbnRfdHlwZSI6ImF1dGhvcml6YXRpb25fY29kZSIsInByb2ZpbGVJZCI6ImM5NzA5ZmIyLTNiMTktNDFiMi1iODYzLTczNzNjZDFjMTNiNSIsInNjb3BlIjoiZ2V0Om5ld3MgZ2V0OnR2IiwiZXhwIjoxNzYwMjA2OTEyLCJpYXQiOjE3NjAxNzgxMTIsImVudGl0eSI6ImhvdXNlaG9sZCIsImp0aSI6Ik1JanhJNlNwRTJCY0FVcWRGbVNqaTFoR0ozWEZKYThIczhBemItZkF3eEUifQ.CNktPa2KTUQpKpJBI9BoYP05gK93HV8CL0L-5U-Ijz1v6KNyAqu3FtiVS7IbxLEIBxn7QpBz3HaixGDGF42GEg; exp_z_at=1760206912; bm_sv=85B07881C96CB70E703262AF8B66DCAB~YAAQDH8mFxVVBJqZAQAAmIjK0h0Ipdlg+1YCzzlgdTPUp/zHL3LcVGS0etSD1D+Bg+ZPyIMJyj3nk9CaUKUOzCJFH0vW6fH5A51tiCHAJGdDQhtZASdiKhF75G/Y0zut+rZP3mn94Ylp3+g/W/gFNuMQPokN/TAg7l6a66c9BgXwPORqxjyGQ3yXTGeijQf9zaxRRzjUTcBLoWvwbfJmD6Prn5MK4eFY/Zp8zOUXac0EeM6RZg0t34mfsz8A~1"""
    cookies_string2="""emergency-mode=0; efm={"sd":"2025-10-09T12:36:29.877Z","ed":"2025-10-16T12:36:29.877Z"}; consentToUse={"status":"optedin","entity":"household","area":{"areaId":"130","jisx0402":"13113","postal":"1508001","pref":"13"}}; bff-rt-authz=cjAyOnJXR2x0S0lxZ0hHZHptZGxqTlNYVCtmQ2ZyZ2gzT0NpNEpUTlhFTDVZMEtNZU1mV2RnRzVZQUQ5R1pJcHdFRU1iZForS040OHcwV0NBT0U9OnZrbHRIOG1PNE1sa1pOM1Q=; exp_z_rt=1762605391; authz_type=r-alaz; area_permanent=130; nhkApVolume=0.7; z_at=eyJhbGciOiJFUzI1NiIsInR5cCI6ImF0K2p3dCIsImtpZCI6ImtpZC1hdXRoei1hYzEtcHJkLTAxIn0.eyJzdWIiOiJjOTcwOWZiMi0zYjE5LTQxYjItYjg2My03MzczY2QxYzEzYjUiLCJpc3MiOiJodHRwczovL3IuYXV0aHouYWMxLm5oayIsImFjdGl2YXRlZEJ5Ijoic2VsZi1hY3RpdmF0ZWQiLCJjbGllbnRfaWQiOiIxMzExNjg5NDQ0MCIsImxpY2Vuc2VUeXBlIjoiMiIsInByb2ZpbGVUeXBlIjoiYW5vbnltb3VzIiwiZ3JhbnRfdHlwZSI6ImF1dGhvcml6YXRpb25fY29kZSIsInByb2ZpbGVJZCI6ImM5NzA5ZmIyLTNiMTktNDFiMi1iODYzLTczNzNjZDFjMTNiNSIsInNjb3BlIjoiZ2V0Om5ld3MgZ2V0OnR2IiwiZXhwIjoxNzYwMzQ3MDg4LCJpYXQiOjE3NjAzMTgyODgsImVudGl0eSI6ImhvdXNlaG9sZCIsImp0aSI6ImZUay1oVTdfb3hKMUdxaFE4NnhvVW9TRDV1RUR2OHJpdmpuN0kyTXRmU2MifQ.Pe-4cyVO2HHCW6maXvXrzMn__sXlB9s5sYEa5yCt_xN45W4Zff4VPlyIOcP2BJD98pj2SH_ik8SD2C3NKBtLBQ; exp_z_at=1760347088; ak_bmsc=41917E8C9203D499BC80EB5C600EA9D3~000000000000000000000000000000~YAAQJn8mF5SVbaOZAQAAonMl2x3meFPAdBiehnIDp2Jcs1JWGJ03wE1oYKNhxHkQl60c+YWTs6TO9zvBVcwk0uvMlKHb6/h+I8jAVD42fRrNrZDetLKCJZ12EgpJQGh5HxXPcMRjUA+VK6P1LvpfbLGCGWkWvDrfaAHELXvPGAmzpkqma5FQl7rv03VsCqufbWKwK6UFfGBUUEz0JKGyG+358nu0TQzxZyQfxhAibtS1jNvDetFPfNmWnuPaLSDd4f6wtutzaM5/SN9folSL8l6qlXoByUuor9n7fYI0wpkyhFfJNYJj4Wc0YjA0o69AVojrZznvycE/SWWY1a7bfI0bz0R5CclzW+y5aiI03s2zB6SldI94f0PsWxr/P2rZEv7Md5OuXmbhywVy/BOXrNK13ePyTSLZrw==; bm_sv=3B12EC18A5E3E1128060AD9198E4FED6~YAAQI38mF83HBpuZAQAABOqL2x2B7xDqe756IlZlAXj6oKlwUMUy/gLL81+r031yIE7LGO53MXKUrbv4dya7G4NboLrWj/eOlYtZO+/sMgArl4I+cwXc7fhwhS/znvR942S3+9DrW8OaBt4KiIPSA1crRnNJqIip85z7ySXSbrnMGGvQxSi1QS4B1eQaNPL9d4G35axwg0ESAXCQteKRTECD2phqbBDLN+GLfvqT9PoSlM/4e/sLFT+zCnQ2sg==~1"""
    # 创建下载器
    downloader = NHKHLSDownloader(m3u8_content2, cookies_string2)
    
    # 开始下载
    output_file = "testaa.m4a"
    success = downloader.download(output_file)
    
    if success:
        print(f"下载完成! 输出文件: {output_file}")
    else:
        print("下载失败!")

if __name__ == "__main__":
    main()
