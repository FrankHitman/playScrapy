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
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import subprocess
from urllib.parse import urlparse, parse_qs, urlunparse, quote

class NHKHLSDownloader:
    def __init__(self, m3u8_content, cookies_string='', base_url=None):
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
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8,zh-CN;q=0.7',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Origin': 'https://news.web.nhk',
            'Referer': 'https://news.web.nhk/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }


        
    def _parse_cookies(self, cookie_string):
        """解析cookie字符串为字典格式"""
        cookies = {}
        if not cookie_string:
            return cookies
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
            response = requests.get(self.key_uri, headers=self.headers, timeout=30)
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
            response = requests.get(segment_url, headers=self.headers, timeout=30)
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
    m3u8_content = """
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:7
#EXT-X-MEDIA-SEQUENCE:1
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-KEY:METHOD=AES-128,URI="https://media.vd.st.nhk/news/easy_audio/ne2025110411598_Fkq1hxsUmCcj8RX3dkHhQIczXjXPo99gHUtyPAlt/serve.key?hdntl=exp=1762770600~acl=/*~data=hdntl~hmac=0e983205854ed6bbb760ac9ab1ab7a00655e5ddefe23e25742f3ca25789d0916&aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_media_format_type=hls"
#EXTINF:6.016,
index_64k_00001.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00002.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=2&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00003.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=3&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00004.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=4&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00005.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=5&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00006.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=6&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00007.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=7&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00008.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=8&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:6.016,
index_64k_00009.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=9&aka_hls_version=3&aka_media_format_type=hls
#EXTINF:2.627,
index_64k_00010.aac?aka_me_session_id=AAAAAAAAAACovhFpAAAAAKL0QdDXk2N1Rjoj4PSUjX%2fzSRZayOwFR91icpEPctVqa5%2fDmL8v%2fTZIL6H2TLCFwjmokx8Re8TF&aka_msn=10&aka_hls_version=3&aka_media_format_type=hls
#EXT-X-ENDLIST

"""

    # 创建下载器
    downloader = NHKHLSDownloader(m3u8_content)
    
    # 开始下载
    output_file = "testaa.m4a"
    success = downloader.download(output_file)
    
    if success:
        print(f"下载完成! 输出文件: {output_file}")
    else:
        print("下载失败!")

if __name__ == "__main__":
    main()
