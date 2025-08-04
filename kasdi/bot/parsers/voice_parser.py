import os
import asyncio
import tempfile
import logging
from typing import Optional
from pathlib import Path

import aiofiles
from aiogram.types import Message
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain_core.documents.base import Blob
from pydub import AudioSegment

from dependencies import configs_obj

# Configuration constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
PROCESSING_TIMEOUT = 30  # seconds
ALLOWED_DURATION = 600  # 10 minutes max

logger = logging.getLogger(__name__)

class VoiceProcessingError(Exception):
    """Base exception for voice processing errors."""
    pass


class FileSizeError(VoiceProcessingError):
    """Raised when file size exceeds limit."""
    pass


class AudioConversionError(VoiceProcessingError):
    """Raised when audio conversion fails."""
    pass


class TranscriptionError(VoiceProcessingError):
    """Raised when transcription fails."""
    pass


class VoiceParser:
    """Voice message parser with transcription capabilities."""

    def __init__(self,
                 api_key: str = None,
                 language: str = "uk",
                 max_file_size: int = MAX_FILE_SIZE,
                 timeout: int = PROCESSING_TIMEOUT,
                 max_duration: int = ALLOWED_DURATION
        ):
        """
        Initialize voice parser.

        :param api_key: OpenAI API key (defaults to config)
        :param language: Language for transcription
        :param max_file_size: Maximum file size in bytes
        :param timeout: Processing timeout in seconds
        :param max_duration: Maximum audio duration in seconds
        """
        self.api_key = api_key or configs_obj.OPENAI_API_KEY
        self.language = language
        self.max_file_size = max_file_size
        self.timeout = timeout
        self.max_duration = max_duration

    async def _download_voice_file(self, message: Message) -> bytes:
        """Download voice file from Telegram with validation."""
        try:
            file_info = await message.bot.get_file(message.voice.file_id)

            if file_info.file_size and file_info.file_size > self.max_file_size:
                raise FileSizeError(f"File size {file_info.file_size} exceeds limit {self.max_file_size}")

            downloaded_file = await message.bot.download_file(file_info.file_path)
            return downloaded_file.read()

        except Exception as e:
            logger.error(f"Failed to download voice file {message.voice.file_id}: {e}")
            raise VoiceProcessingError(f"Download failed: {e}")

    async def _convert_audio_to_mp3(self, ogg_data: bytes, temp_dir: str) -> str:
        """Convert OGG audio data to MP3 format asynchronously."""
        try:
            ogg_path = Path(temp_dir) / "audio.ogg"
            mp3_path = Path(temp_dir) / "audio.mp3"

            async with aiofiles.open(ogg_path, "wb") as f:
                await f.write(ogg_data)

            audio = AudioSegment.from_ogg(str(ogg_path))

            duration_seconds = len(audio) / 1000
            if duration_seconds > self.max_duration:
                raise AudioConversionError(f"Audio duration {duration_seconds}s exceeds limit {self.max_duration}s")

            audio.export(str(mp3_path), format="mp3", bitrate="128k")
            return str(mp3_path)

        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")
            raise AudioConversionError(f"Audio conversion failed: {e}")

    async def _transcribe_audio(self, mp3_path: str) -> str:
        """Transcribe audio file using OpenAI Whisper."""
        try:
            whisper_parser = OpenAIWhisperParser(
                api_key=self.api_key,
                language=self.language,
            )

            transcription = whisper_parser.parse(Blob(path=mp3_path))
            transcription_parts = [doc.page_content for doc in transcription if doc.page_content]

            if not transcription_parts:
                return ""

            return " ".join(transcription_parts).strip()

        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise TranscriptionError(f"Transcription failed: {e}")

    async def process_voice_message(self, message: Message) -> Optional[str]:
        """
        Process voice message and return transcribed text.

        :param message: Telegram message with voice attachment
        :return: Transcribed text or None if processing fails
        """
        if not message.voice:
            return None

        temp_dir = None

        try:
            temp_dir = tempfile.mkdtemp(prefix="voice_")

            async with asyncio.timeout(self.timeout):
                logger.info(f"Downloading voice file {message.voice.file_id}")
                ogg_data = await self._download_voice_file(message)

                logger.info("Converting audio to MP3 format")
                mp3_path = await self._convert_audio_to_mp3(ogg_data, temp_dir)

                logger.info("Transcribing audio")
                text = await self._transcribe_audio(mp3_path)

                logger.info(f"Successfully transcribed voice message: {len(text)} characters")
                return text if text else None

        except asyncio.TimeoutError:
            logger.error(f"Voice processing timeout after {self.timeout}s")
            return None

        except FileSizeError as e:
            logger.warning(f"File size error: {e}")
            return None

        except (AudioConversionError, TranscriptionError) as e:
            logger.error(f"Processing error: {e}")
            return None

        except VoiceProcessingError as e:
            logger.error(f"Voice processing error: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error processing voice message: {e}")
            return None

        finally: # Cleanup temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary directory {temp_dir}: {e}")


_default_parser = VoiceParser()


async def process_voice_message(message: Message) -> Optional[str]:
    """
    Backward compatibility function for existing code.

    Args:
        message: Telegram message with voice attachment

    Returns:
        Transcribed text or None if processing fails
    """
    return await _default_parser.process_voice_message(message)


