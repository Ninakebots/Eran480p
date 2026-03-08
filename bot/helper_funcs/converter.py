import os
import logging
from bot.helper_funcs.ffmpeg import (
    convert_video,
    convert_video_all,
    convert_video_custom,
    add_hard_subtitles,
    cut_video
)

LOGGER = logging.getLogger(__name__)

FIX_FLAGS = ['-fflags', '+genpts', '-ignore_unknown']

async def convert_video_robust(video_file, output_directory, total_time, bot, message, settings=None):
    """Robust wrapper for convert_video with retry and fix flags."""
    # Attempt 1
    result = await convert_video(video_file, output_directory, total_time, bot, message, settings=settings)

    if result and os.path.exists(result):
        return result

    # Attempt 2 with fix flags
    LOGGER.warning(f"Conversion failed for {video_file}. Retrying with fix flags...")
    return await convert_video(
        video_file, output_directory, total_time, bot, message,
        settings=settings, extra_args=FIX_FLAGS
    )

async def convert_video_all_robust(video_file, output_directory, total_time, bot, message, settings=None):
    """Robust wrapper for convert_video_all with retry and fix flags."""
    # Attempt 1
    results = await convert_video_all(video_file, output_directory, total_time, bot, message, settings=settings)

    if results:
        return results

    # Attempt 2 with fix flags
    LOGGER.warning(f"Multi-resolution encoding failed for {video_file}. Retrying with fix flags...")
    return await convert_video_all(
        video_file, output_directory, total_time, bot, message,
        settings=settings, extra_args=FIX_FLAGS
    )

async def convert_video_custom_robust(video_file, output_directory, total_time, bot, message, ffmpegcode):
    """Robust wrapper for convert_video_custom with retry and fix flags."""
    # Attempt 1
    result = await convert_video_custom(video_file, output_directory, total_time, bot, message, ffmpegcode)

    if result and os.path.exists(result):
        return result

    # Attempt 2 with fix flags
    LOGGER.warning(f"Custom conversion failed for {video_file}. Retrying with fix flags...")
    return await convert_video_custom(
        video_file, output_directory, total_time, bot, message,
        ffmpegcode, extra_args=FIX_FLAGS
    )

async def add_hard_subtitles_robust(video_file, subtitle_file, output_directory, bot, message, settings=None):
    """Robust wrapper for add_hard_subtitles with retry and fix flags."""
    # Attempt 1
    result = await add_hard_subtitles(video_file, subtitle_file, output_directory, bot, message, settings=settings)

    if result and os.path.exists(result):
        return result

    # Attempt 2 with fix flags
    LOGGER.warning(f"Adding hard subtitles failed for {video_file}. Retrying with fix flags...")
    return await add_hard_subtitles(
        video_file, subtitle_file, output_directory, bot, message,
        settings=settings, extra_args=FIX_FLAGS
    )

async def cut_video_robust(video_file, output_directory, start_time, end_time, bot, message, settings=None):
    """Robust wrapper for cut_video with retry and fix flags."""
    # Attempt 1
    result = await cut_video(video_file, output_directory, start_time, end_time, bot, message, settings=settings)

    if result and os.path.exists(result):
        return result

    # Attempt 2 with fix flags
    LOGGER.warning(f"Trimming failed for {video_file}. Retrying with fix flags...")
    return await cut_video(
        video_file, output_directory, start_time, end_time, bot, message,
        settings=settings, extra_args=FIX_FLAGS
    )
