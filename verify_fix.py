import logging
import os

# Mock LOGGER
class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")

LOGGER = MockLogger()

def test_logging(video, o, caption):
    print(f"Testing with video={video}, o={o}, caption={caption}")

    # Simulate step 1 changes
    if video:
        LOGGER.info(f"Downloaded video path: {video}")
    else:
        LOGGER.info("Download failed or was cancelled, video path is None")

    if o:
        LOGGER.info(f"Compression successful: {o}")
    else:
        LOGGER.info("Compression failed, output path is None")

    if caption:
        LOGGER.info(f"Final caption: {caption}")
    else:
        LOGGER.warning("Upload successful but message or caption is None")

print("--- Case 1: All None ---")
test_logging(None, None, None)

print("\n--- Case 2: All OK ---")
test_logging("/path/to/video", "/path/to/output", "Success!")
