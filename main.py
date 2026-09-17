from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import yt_dlp

app = FastAPI(
    title="Universal Media Downloader API",
    description="Backend API for extract video links & formats using yt-dlp",
    version="1.0.0"
)

# السماح لجميع المصادر بالاتصال (CORS) لضمان اتصالات التطبيق بدون مشاكل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نماذج البيانات (Data Models)
class FormatOption(BaseModel):
    format_id: str
    extension: str
    resolution: str
    filesize_approx: Optional[int] = None
    url: str
    has_audio: bool
    has_video: bool

class VideoInfoResponse(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    formats: List[FormatOption]

@app.get("/")
def read_root():
    return {"status": "online", "message": "Media Downloader API is running successfully"}

@app.get("/api/extract", response_model=VideoInfoResponse)
def extract_video_info(url: str = Query(..., description="رابط الفيديو المراد معالجته")):
    """
    استخراج معلومات الفيديو وجودات التنزيل المتاحة
    """
    if not url:
        raise HTTPException(status_code=400, detail="يرجى إرسال رابط فيديو صحيح")

    # إعدادات yt-dlp لاستخراج المعلومات فقط دون تنزيل الملف على السيرفر
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            
            # معالجة قائمة الجودات والصيغ المتوفرة
            for fmt in info.get('formats', []):
                format_url = fmt.get('url')
                if not format_url:
                    continue

                ext = fmt.get('ext', 'mp4')
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                
                has_video = vcodec != 'none'
                has_audio = acodec != 'none'
                
                # تحديد الدقة
                resolution = fmt.get('resolution')
                if not resolution:
                    height = fmt.get('height')
                    resolution = f"{height}p" if height else "Audio Only" if not has_video else "Unknown"

                formats_list.append(
                    FormatOption(
                        format_id=str(fmt.get('format_id', '')),
                        extension=ext,
                        resolution=resolution,
                        filesize_approx=fmt.get('filesize') or fmt.get('filesize_approx'),
                        url=format_url,
                        has_audio=has_audio,
                        has_video=has_video
                    )
                )

            return VideoInfoResponse(
                id=str(info.get('id', '')),
                title=info.get('title', 'Video'),
                thumbnail=info.get('thumbnail'),
                duration=info.get('duration'),
                uploader=info.get('uploader'),
                formats=formats_list
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء معالجة الرابط: {str(e)}")
      
