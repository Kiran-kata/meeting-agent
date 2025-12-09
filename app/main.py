import sys
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from .overlay import Overlay
from .agent import MeetingAgentCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/meeting_agent.log', mode='a')
    ]
)


# Adjust these indices once after checking sounddevice.query_devices()
MEETING_DEVICE_INDEX = 24  # Stereo Mix (Realtek HD Audio Stereo input) - captures system audio
MIC_DEVICE_INDEX = 2       # Microphone (OMEN Cam & Voice)


def main():
    app = QApplication(sys.argv)

    overlay = Overlay()
    overlay.show_message("Meeting Agent\n\nClick Start to begin recording")

    agent = MeetingAgentCore(
        overlay_widget=overlay,
        meeting_device_index=MEETING_DEVICE_INDEX,
        mic_device_index=MIC_DEVICE_INDEX,
    )

    def start_agent():
        agent.start()
        overlay.show_message(
            "Meeting agent running.\n\n"
            "- Listening to meeting audio (for questions)\n"
            "- Listening to your mic (ignored for Q&A)\n"
            "- Scanning screen & PDFs\n"
            "Click Stop to end and generate summary."
        )

    def stop_agent():
        agent.stop()
        overlay.show_message("Meeting stopped.\nGenerating summary...")
        summary_path = agent.generate_summary_and_save()
        overlay.show_message(f"Summary saved:\n{summary_path}")

    # Connect overlay signals to agent
    overlay.start_requested.connect(start_agent)
    overlay.stop_requested.connect(stop_agent)

    def on_about_to_quit():
        if agent.running:
            agent.stop()

    app.aboutToQuit.connect(on_about_to_quit)

    overlay.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
