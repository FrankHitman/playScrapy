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

if __name__ == "__main__":
    key_url = 'https://media.vd.st.nhk/news/easy_audio/ne2025101012062_veGbQ9D7MZGDNIUGzqW97D35WRBjpUSYCUrDy9Sf/serve.key?hdntl=exp=1760413473~acl=/*~data=hdntl~hmac=306b8ecbaedcaf7ae5160b935f5973704be9a16ab9a1a5e8a8363e2e827729ec&aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_media_format_type=hls'
    segment_url = 'index_64k_00001.aac?aka_me_session_id=AAAAAAAAAAAhx+1oAAAAAEp1UQTNFxR5835yZvkInCCcDpqUGkuHhTpJRJL9Y8oCB46ohLFdX6B%2fEWZ1IR6itGJmEFJPCWCY&aka_msn=1&aka_hls_version=3&aka_media_format_type=hls'
    print(build_media_url(key_url, segment_url))