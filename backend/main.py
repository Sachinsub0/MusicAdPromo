import atexit
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from posthog import Posthog
from posthog.integrations.asgi import PosthogASGIMiddleware
from pydantic import BaseModel

from backend.config import get_settings
from shared.alignment_v7 import align_clip, validate_words
from shared.audio import clip_audio, load_audio, propose_hooks, wav_bytes
from shared.render_v7 import TEMPLATES, render_mp4

logger = logging.getLogger(__name__)
posthog_logs_logger = logging.getLogger("musicadpromo.posthog_logs")
posthog_logs_logger.setLevel(logging.INFO)
posthog_logs_logger.propagate = False
settings = get_settings()
posthog_client = None
posthog_logs_provider = None


def configure_posthog_log_export():
    """Configure an isolated OTLP logger for purpose-written app logs only."""
    if not settings.posthog_project_token or not settings.posthog_host:
        return None

    provider = LoggerProvider()
    exporter = OTLPLogExporter(
        endpoint=f"{settings.posthog_host.rstrip('/')}/i/v1/logs",
        headers={"Authorization": f"Bearer {settings.posthog_project_token}"},
    )
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    posthog_logs_logger.addHandler(
        LoggingHandler(level=logging.INFO, logger_provider=provider)
    )
    return provider


if settings.posthog_project_token and settings.posthog_host:
    posthog_client = Posthog(
        settings.posthog_project_token,
        host=settings.posthog_host,
        enable_exception_autocapture=True,
    )
    atexit.register(posthog_client.shutdown)
    posthog_logs_provider = configure_posthog_log_export()
elif os.getenv("ENVIRONMENT") != "production":
    for variable in (
        "POSTHOG_PROJECT_TOKEN",
        "POSTHOG_HOST",
    ):
        if not getattr(settings, variable.lower()):
            logger.warning(
                "%s variable required by PostHog is missing or un-configured, this causes events to be silently missed. "
                "This error stops appearing once %s is configured",
                variable,
                variable,
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    posthog_logs_logger.info("music_ad_promo_api_started")
    yield
    if posthog_client:
        try:
            posthog_client.flush()
        except Exception:
            logger.warning("PostHog flush failed during shutdown", exc_info=True)
    if posthog_logs_provider:
        try:
            posthog_logs_provider.force_flush(timeout_millis=3000)
            posthog_logs_provider.shutdown(timeout_millis=3000)
        except Exception:
            logger.warning("PostHog log flush failed during shutdown", exc_info=True)


app = FastAPI(title="MusicAdPromo v7 API", lifespan=lifespan)
if posthog_client:
    app.add_middleware(PosthogASGIMiddleware, client=posthog_client)

MAX_BYTES=200*1024*1024


def capture_event(event: str, properties: dict) -> None:
    """Capture optional analytics without affecting media processing."""
    if not posthog_client:
        return
    try:
        posthog_client.capture(event, properties=properties)
    except Exception:
        logger.warning("PostHog capture failed for %s", event, exc_info=True)


async def receive(audio):
    # UploadFile is a SpooledTemporaryFile: check its size without reading
    # an oversized upload into another large bytes object.
    await audio.seek(0)
    audio.file.seek(0, os.SEEK_END)
    size=audio.file.tell()
    await audio.seek(0)
    if size>MAX_BYTES:
        raise HTTPException(413,f'Audio file exceeds 200 MB ({size/1024/1024:.1f} MB received)')
    data=await audio.read()
    try:return load_audio(data, filename=audio.filename or "upload.mp3")
    except Exception as e:raise HTTPException(422,f'Unable to decode audio: {e}')

@app.get('/health')
def health():return {'status':'ok','version':'7-starter'}

@app.post('/v7/hooks')
async def hooks(audio:UploadFile=File(...),duration:int=Form(15)):
    if not 10<=duration<=25:raise HTTPException(422,'Duration must be 10–25 seconds')
    y,sr=await receive(audio)
    try:choices=propose_hooks(y,sr,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    capture_event(
        "hook_recommendations_generated",
        {"duration_seconds": duration, "recommendation_count": len(choices)},
    )
    posthog_logs_logger.info(
        "hook_recommendations_ready",
        extra={"duration_seconds": duration, "recommendation_count": len(choices)},
    )
    return {'duration':round(len(y)/sr,2),'hooks':choices,'method':'RMS + onset heuristic'}

@app.post('/v7/preview')
async def preview(audio:UploadFile=File(...),start:float=Form(...),duration:int=Form(15)):
    y,sr=await receive(audio)
    try:segment=clip_audio(y,sr,start,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    preview_audio = wav_bytes(segment,sr)
    capture_event("audio_preview_generated", {"duration_seconds": duration})
    return Response(preview_audio,media_type='audio/wav')

@app.post('/v7/align')
async def align(audio:UploadFile=File(...),start:float=Form(...),duration:int=Form(15),lyrics:str=Form(''),language:str=Form('')):
    y,sr=await receive(audio)
    try:segment=clip_audio(y,sr,start,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:
        f.write(wav_bytes(segment,sr));path=f.name
    try:
        result = align_clip(path,lyrics,language)
        capture_event(
            "clip_transcribed",
            {
                "duration_seconds": duration,
                "word_count": len(result.get("words", [])),
                "language_provided": bool(language),
            },
        )
        posthog_logs_logger.info(
            "clip_transcription_completed",
            extra={
                "duration_seconds": duration,
                "word_count": len(result.get("words", [])),
                "language_provided": bool(language),
            },
        )
        return result
    except RuntimeError as e:raise HTTPException(503,str(e))
    finally:os.unlink(path)

class TimingPayload(BaseModel):
    duration:float
    words:list[dict]

@app.post('/v7/validate-timings')
def validate_timings(payload:TimingPayload):
    try:
        words = validate_words(payload.words,payload.duration)
        capture_event(
            "lyric_timings_validated",
            {"duration_seconds": payload.duration, "word_count": len(words)},
        )
        return {'words':words}
    except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))

@app.get('/v7/templates')
def templates():
    return {'templates':TEMPLATES}

@app.post('/v7/render')
async def render(audio:UploadFile=File(...),start:float=Form(...),duration:int=Form(15),template:str=Form('skyline'),words_json:str=Form('[]')):
    if not 10<=duration<=25:raise HTTPException(422,'Duration must be 10–25 seconds')
    if template not in TEMPLATES:raise HTTPException(422,'Invalid scene template')
    try:
        words=json.loads(words_json)
        if not isinstance(words,list):raise ValueError('words_json must be a list')
        words=validate_words(words,duration)
    except (ValueError,TypeError,KeyError) as exc:raise HTTPException(422,f'Invalid lyric timings: {exc}')
    y,sr=await receive(audio)
    try:
        segment=clip_audio(y,sr,start,duration)
        data=render_mp4(segment,sr,template,words)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except Exception as exc:raise HTTPException(500,f'Video rendering failed: {exc}')
    capture_event(
        "promo_video_rendered",
        {
            "duration_seconds": duration,
            "template": template,
            "word_count": len(words),
        },
    )
    posthog_logs_logger.info(
        "promo_video_render_completed",
        extra={
            "duration_seconds": duration,
            "template": template,
            "word_count": len(words),
        },
    )
    return Response(content=data,media_type='video/mp4',headers={'Content-Disposition':'attachment; filename="musicadpromo-v7.mp4"'})
