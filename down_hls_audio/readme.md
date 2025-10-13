# HLS

## cause
I want to make some Japanese shadowing videos which using some resources from [NHK](https://news.web.nhk/news/easy).

The audio resources are not a single file. So that I inspect the implementation of this website. And I found the HTTP Live Streaming Protocol.

Below are my chat with ChatGPT

## 请问 HTTP Live Streaming 技术是什么？实现原理是什么

HTTP Live Streaming（简称 **HLS**）是由 **Apple（苹果公司）** 提出的一个**基于 HTTP 的流媒体传输协议**，广泛应用于视频直播与点播（例如 YouTube、哔哩哔哩、抖音等）中。它的核心思想是：**把连续的视频流切成很多小文件（通常几秒一个），客户端通过普通的 HTTP 请求顺序下载并播放这些小文件。**

---

### 一、HLS 的基本概念

| 项目       | 说明                                                     |
| -------- | ------------------------------------------------------ |
| **全称**   | HTTP Live Streaming                                    |
| **提出方**  | Apple（2009年，与 iOS 一起推出）                                |
| **协议层**  | 应用层（基于 HTTP/1.1 或 HTTP/2）                              |
| **使用场景** | 视频直播、点播、监控回放、教育流媒体等                                    |
| **传输格式** | 通常为 MPEG-TS（Transport Stream）或 fMP4                    |
| **播放支持** | iOS/macOS 原生支持，Android、浏览器可通过播放器库（如 hls.js、video.js）播放 |

---

### 二、HLS 的工作原理

HLS 的实现分为三个关键部分：

#### 1. **流切片（Segmenting）**

* 编码器或服务器将视频流（如 RTMP）分割成**小段文件**（Segment）。
* 每个小文件通常长度为 **2~10秒**（常见为 6 秒）。
* 常见文件格式：

  * `.ts`（MPEG-TS）
  * `.m4s`（fMP4 格式）
* 例如：

  ```
  segment_000.ts
  segment_001.ts
  segment_002.ts
  ...
  ```

#### 2. **播放列表文件（Manifest）**

* 播放列表是一个 `.m3u8` 文件，描述了视频分片的顺序与地址。

* 例如：

  ```m3u8
  #EXTM3U
  #EXT-X-VERSION:3
  #EXT-X-TARGETDURATION:6
  #EXT-X-MEDIA-SEQUENCE:0
  #EXTINF:6.0,
  segment_000.ts
  #EXTINF:6.0,
  segment_001.ts
  #EXTINF:6.0,
  segment_002.ts
  ```

* 对于**直播流（Live）**：

  * `.m3u8` 文件不断更新，只保留最近的几个分片。

* 对于**点播（VOD）**：

  * `.m3u8` 文件是固定的，包含全部分片。

#### 3. **客户端播放（Client Playback）**

* 客户端通过 HTTP 下载 `.m3u8` 文件；
* 解析其中的分片地址；
* 按顺序下载 `.ts` 文件并播放；
* 对于直播流，客户端会**周期性刷新 `.m3u8` 文件**，以获取新的视频分片。

---

### 三、HLS 的数据流结构

```
┌──────────────┐
│  推流端(OBS) │  →  RTMP/RTSP
└──────┬───────┘
       ↓
┌───────────────────────────┐
│  转码/切片服务器 (FFmpeg) │
│  输出：segment_000.ts      │
│        playlist.m3u8        │
└──────┬────────────────────┘
       ↓
┌───────────────────────────┐
│   HTTP 服务器 (Nginx+HLS) │
│   提供HTTP访问接口         │
└──────┬────────────────────┘
       ↓
┌───────────────────────────┐
│   客户端 (浏览器、手机)    │
│   下载m3u8→下载ts→播放     │
└───────────────────────────┘
```

---

### 四、优点与缺点

| 优点               | 说明                           |
| ---------------- | ---------------------------- |
| ✅ **HTTP 传输**    | 不需要特殊协议，直接走 HTTP/CDN，易于穿透防火墙 |
| ✅ **自适应码率（ABR）** | 客户端可根据网络状况自动切换不同质量的流         |
| ✅ **兼容性好**       | iOS、Safari、主流播放器天然支持         |
| ✅ **可缓存**        | 可利用 CDN 缓存每个分片文件，降低服务器压力     |

| 缺点          | 说明                          |
| ----------- | --------------------------- |
| ❌ **延迟较高**  | 因为分片机制（每个片6秒），延迟通常在10~30秒之间 |
| ❌ **启动慢**   | 需要下载多个分片才能开始播放              |
| ❌ **实时性不足** | 不适合对延迟要求极高的场景（如视频会议）        |

---

### 五、示例：使用 FFmpeg 生成 HLS

```bash
ffmpeg -i input.mp4 \
  -codec: copy \
  -start_number 0 \
  -hls_time 6 \
  -hls_list_size 0 \
  -f hls playlist.m3u8
```

生成：

```
playlist.m3u8
segment_000.ts
segment_001.ts
segment_002.ts
...
```

---

### 六、HLS 与其他流媒体协议的比较

| 协议         | 基于   | 延迟     | 是否自适应 | 传输方式   | 典型用途            |
| ---------- | ---- | ------ | ----- | ------ | --------------- |
| **HLS**    | HTTP | 10~30s | ✅     | 文件（TS） | 点播、直播           |
| **DASH**   | HTTP | 5~15s  | ✅     | fMP4   | YouTube、Netflix |
| **RTMP**   | TCP  | 1~3s   | ❌     | 流式     | 推流、实时互动         |
| **WebRTC** | UDP  | <1s    | ✅     | 实时数据通道 | 会议、连麦           |


## 请帮我分析下这两个链接是实现了 HLS 了吗？
```
https://media.vd.st.nhk/news/easy_audio/ne2025101017047_4IoalMQ7I5LORUIVdT34ExOCPsoXNKeSeEYMwuSy/serve.key?hdntl=exp=1760252604~acl=/*~data=hdntl~hmac=f5e9451883dcd77af57187ffbfa2f76a9d1bb205cebd0fa082bd096393275397&aka_me_session_id=AAAAAAAAAAC8UutoAAAAAJDKkS9prc1E1WiPCMtja4Fw7azpui1LltfUFn6hkouh%2f0GLsN7J0uRn9GxYCABpR2FEey0vo8Iv&aka_media_format_type=hls

https://media.vd.st.nhk/news/easy_audio/ne2025101017047_4IoalMQ7I5LORUIVdT34ExOCPsoXNKeSeEYMwuSy/hdntl=exp=1760252604~acl=%2f*~data=hdntl~hmac=f5e9451883dcd77af57187ffbfa2f76a9d1bb205cebd0fa082bd096393275397/index_64k_00010.aac?aka_me_session_id=AAAAAAAAAAC8UutoAAAAAJDKkS9prc1E1WiPCMtja4Fw7azpui1LltfUFn6hkouh%2f0GLsN7J0uRn9GxYCABpR2FEey0vo8Iv&aka_msn=10&aka_hls_version=3&aka_media_format_type=hls
```

非常好的问题。
你提供的这两个链接确实显示出 **典型的 HLS（HTTP Live Streaming）结构**，下面我们逐一拆解分析。

---

### 一、先看两个链接的结构

#### 1️⃣ `serve.key`

```
https://media.vd.st.nhk/news/easy_audio/ne2025101017047_.../serve.key?...hmac=...
```

**推测：**
这是一个 **加密密钥文件（.key）**，用于 HLS 的 **AES-128 或 SAMPLE-AES 加密机制**。

在加密的 HLS 流中，播放列表（`.m3u8`）文件通常会包含类似这样的行：

```m3u8
#EXT-X-KEY:METHOD=AES-128,URI="https://media.vd.st.nhk/.../serve.key"
```

这个 `.key` 文件是客户端（播放器）在解码 `.ts` 或 `.aac` 音频分片时用来解密的密钥。

---

#### 2️⃣ `index_64k_00010.aac`

```
https://media.vd.st.nhk/news/easy_audio/ne2025101017047_.../index_64k_00010.aac?...aka_media_format_type=hls
```

这条 URL 指向一个 `.aac` 文件，后缀 `_00010` 表明这是一个 **分片文件（Segment）**。
`aka_media_format_type=hls` 进一步说明它属于 HLS 播放格式。

分片命名规律通常是：

```
index_64k_00000.aac
index_64k_00001.aac
index_64k_00002.aac
...
```

这些分片文件通常在 `.m3u8` 播放列表中被顺序引用。

---

### 二、结合来看 —— HLS 的完整结构应如下：

在 NHK 的服务器上，完整的 HLS 结构大致是：

```
/news/easy_audio/ne2025101017047_4IoalMQ7I5LORUIVdT34ExOCPsoXNKeSeEYMwuSy/
├── master.m3u8          ← 主播放列表（多码率）
├── index_64k.m3u8       ← 某一音频码率（如64kbps）的子列表
├── index_64k_00000.aac  ← 音频分片1
├── index_64k_00001.aac  ← 音频分片2
├── ...
├── serve.key            ← AES加密密钥
```

---

### 三、判断依据总结

| 文件类型   | 特征                                                  | 作用            | 是否属于 HLS |
| ------ | --------------------------------------------------- | ------------- | -------- |
| `.key` | 含有 AES 密钥，URL 中带有加密参数（exp, hmac）                    | 解密分片          | ✅ 是      |
| `.aac` | 带 `_00010` 这样的分片编号，参数中有 `aka_media_format_type=hls` | 音频分片（Segment） | ✅ 是      |

**→ 结论：这两个链接确实是 HLS 流的一部分。**

---

### 四、补充：完整播放链推测

1. 播放器（如 nhk easy news app）首先访问：

   ```
   index_64k.m3u8
   ```
2. `.m3u8` 文件内容示例（简化）：

   ```m3u8
   #EXTM3U
   #EXT-X-TARGETDURATION:10
   #EXT-X-KEY:METHOD=AES-128,URI="https://media.vd.st.nhk/.../serve.key"
   #EXTINF:10.0,
   index_64k_00010.aac
   #EXTINF:10.0,
   index_64k_00011.aac
   ...
   ```
3. 播放器下载 `.key` 文件，解密 `.aac` 音频分片。
4. 解密后按顺序拼接播放音频流。

---

### 五、总结一句话说明：

> 是的，这两个链接属于 NHK 的 **HLS 流媒体系统**：
> `.key` 文件是加密密钥，`.aac` 文件是分片音频内容，
> 它们都通过 `.m3u8` 播放列表组合实现基于 HTTP 的分段传输播放。

## 以下是m3u8文件和相应的请求链接吗？
```
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-STREAM-INF:BANDWIDTH=64710,AVERAGE-BANDWIDTH=64250,CODECS="mp4a.40.5"
hdntl=exp=1760267440~acl=%2f*~data=hdntl~hmac=d4c8373db47aa78e836a0364b328906a149cfef8477ab7af22754ac74c007aed/index_64k.m3u8?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_media_format_type=hls


https://media.vd.st.nhk/news/easy_audio/ne2025101017047_4IoalMQ7I5LORUIVdT34ExOCPsoXNKeSeEYMwuSy/index.m3u8?hdnts=exp=1760181452~acl=/*~hmac=66abc2f9e650d58306b53e958ea41e9874046c03e4858dc480092349d4dabbdb
```

非常好，这次你提供的这两个 `.m3u8` 文件正是 HLS 的 **核心播放列表文件**，我们来仔细拆解。

---

### 一、两个文件的作用区别

| 文件                   | 类型                     | 作用                                                     |
| -------------------- | ---------------------- | ------------------------------------------------------ |
| **`index.m3u8`**     | 主播放列表（Master Playlist） | 指定了所有可用的码率 / 版本（例如 64kbps, 128kbps），播放器根据网络条件选择合适的子列表。 |
| **`index_64k.m3u8`** | 媒体播放列表（Media Playlist） | 列出了音频分片文件（`.aac`）的顺序与时长。                               |

---

### 二、`index.m3u8` 内容分析（你贴的第一个）

```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-STREAM-INF:BANDWIDTH=64710,AVERAGE-BANDWIDTH=64250,CODECS="mp4a.40.5"
hdntl=exp=1760267440~acl=%2f*~data=hdntl~hmac=d4c8373db47aa78e836a0364b328906a149cfef8477ab7af22754ac74c007aed/index_64k.m3u8?aka_me_session_id=AAAAAAAAAACwjOtoAAAAAN6h5xsIs1%2fcA6%2fOJnHVxQNl4wn8CxHoVAcK5pkZmNzz5BKbsD1Od9hxf69Z+SyjTUp%2f6MsiCRwY&aka_media_format_type=hls
```

#### 说明：

| 指令                            | 含义                                   |
| ----------------------------- | ------------------------------------ |
| `#EXTM3U`                     | M3U8 文件标头（必须）                        |
| `#EXT-X-VERSION:3`            | HLS 版本号（3 支持浮点时长、兼容主流播放器）            |
| `#EXT-X-INDEPENDENT-SEGMENTS` | 表示分片之间相互独立（可单独解码）                    |
| `#EXT-X-STREAM-INF`           | 描述一个可播放流的参数                          |
| `BANDWIDTH`                   | 最大带宽（单位：bps）                         |
| `AVERAGE-BANDWIDTH`           | 平均带宽                                 |
| `CODECS="mp4a.40.5"`          | AAC 音频编码                             |
| 下一行                           | 指向实际的媒体列表文件 `index_64k.m3u8`（音频分片清单） |

---

### 三、主播放列表的作用

播放器（如 Safari、hls.js、NHK Easy News App）会：

1. 下载 `index.m3u8`
2. 解析其中的 `#EXT-X-STREAM-INF` 行
   → 发现有一个码率为 64kbps 的流
3. 下载并播放：

   ```
   index_64k.m3u8
   ```

---

### 四、第二个链接

```
https://media.vd.st.nhk/news/easy_audio/ne2025101017047_.../index.m3u8?hdnts=exp=...~hmac=...
```

这个是上面分析的 **主播放列表** 的完整访问 URL。
其中的 `hdnts=exp=...~hmac=...` 是 **Akamai CDN 的授权签名参数**（防盗链机制）。

* `exp=1760181452`：过期时间（Unix 时间戳）
* `hmac=66abc2f9...`：签名校验
* `hdnts`：Akamai 的令牌认证字段（HTTP Dynamic Tokenization）

---

### 五、完整的 HLS 播放流程（NHK Easy Audio 示例）

```
index.m3u8                    ← 主播放列表
 └─ index_64k.m3u8            ← 媒体播放列表
     ├─ #EXT-X-KEY:URI=serve.key  ← 可选（如果加密）
     ├─ index_64k_00000.aac
     ├─ index_64k_00001.aac
     ├─ index_64k_00002.aac
     └─ ...
```

客户端播放时：

1. 下载 `index.m3u8`
2. 选择合适码率（这里只有 64kbps）
3. 下载 `index_64k.m3u8`
4. 依次请求 `.aac` 音频分片（如 `_00000.aac`）
5. 如果有加密（`#EXT-X-KEY`），则还会请求 `serve.key`
6. 将分片解密并连续播放

---

### 六、结论

| 项目           | 结论                              |
| ------------ | ------------------------------- |
| **是否 HLS？**  | ✅ 是，符合 HLS 结构（主列表 + 媒体列表 + 分片）  |
| **类型**       | 音频 HLS（仅 AAC，无视频）               |
| **CDN 授权机制** | Akamai 动态令牌（`hdnts`, `hmac`）    |
| **版本**       | HLS v3（兼容 Safari、Chrome、移动端播放器） |
| **播放形式**     | 分段下载 + 连续播放，实现低带宽音频流            |

---

如果你想，我可以帮你用 **Python + ffmpeg** 或 **Python + m3u8 库** 写一个脚本来：

* 自动解析主 `.m3u8`
* 下载所有 `.aac` 分片
* （如果未加密）合并为一个完整音频文件（如 `.m4a`）


## Update
through observing the request and response in the browser

m3u8 response contains serve.key and slice information like below:
```
https://media.vd.st.nhk/news/easy_audio/ne2025101012062_veGbQ9D7MZGDNIUGzqW97D35WRBjpUSYCUrDy9Sf/serve.key?hdntl=exp=1760413473~acl=/*~data=hdntl~hmac=306b8ecbaedcaf7ae5160b935f5973704be9a16ab9a1a5e8a8363e2e827729ec&aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_media_format_type=hls

index_64k_00001.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls

```

the successful request url is like below, which contains the parameters already stored in m3u8:
```
https://media.vd.st.nhk/news/easy_audio/ne2025101012062_veGbQ9D7MZGDNIUGzqW97D35WRBjpUSYCUrDy9Sf/hdntl=exp=1760413473~acl=%2f*~data=hdntl~hmac=306b8ecbaedcaf7ae5160b935f5973704be9a16ab9a1a5e8a8363e2e827729ec/index_64k_00001.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls
```

So introduce new function to convert the url:
```
from urllib.parse import urlparse, parse_qs, urlunparse, quote

def build_media_url(key_url: str, segment_url: str) -> str:
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


```
