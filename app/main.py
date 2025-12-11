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

logger = logging.getLogger(__name__)

# Adjust these indices once after checking sounddevice.query_devices()
MEETING_DEVICE_INDEX = 0   # Microsoft Sound Mapper (default input device)
MIC_DEVICE_INDEX = 2       # Microphone (OMEN Cam & Voice)


def main():
    try:
        app = QApplication(sys.argv)

        overlay = Overlay()
        overlay.show_message("Meeting Agent\n\nClick Start to begin recording")

        agent = MeetingAgentCore(
            overlay_widget=overlay,
            meeting_device_index=MEETING_DEVICE_INDEX,
            mic_device_index=MIC_DEVICE_INDEX,
        )

        def start_agent():
            try:
                logger.info("User clicked Start button")
                agent.start()
                overlay.show_message(
                    "Meeting agent running.\n\n"
                    "- Listening to meeting audio (for questions)\n"
                    "- Listening to your mic (ignored for Q&A)\n"
                    "- Scanning screen & PDFs\n"
                    "Click Stop to end and generate summary."
                )
            except Exception as e:
                logger.error(f"Error starting agent: {e}", exc_info=True)
                overlay.show_message(f"Error starting: {str(e)}\n\nCheck logs for details.")

        def stop_agent():
            try:
                logger.info("User clicked Stop button")
                agent.stop()
                overlay.show_message("Meeting stopped.\nGenerating summary...")
                summary_path = agent.generate_summary_and_save()
                overlay.show_message(f"Summary saved:\n{summary_path}")
            except Exception as e:
                logger.error(f"Error stopping agent: {e}", exc_info=True)
                overlay.show_message(f"Error stopping: {str(e)}\n\nCheck logs for details.")

        # Connect overlay signals to agent
        overlay.start_requested.connect(start_agent)
        overlay.stop_requested.connect(stop_agent)
        overlay.pdf_selected.connect(agent.add_pdf_file)  # Connect PDF upload signal

        def on_about_to_quit():
            try:
                if agent.running:
                    agent.stop()
            except Exception as e:
                logger.error(f"Error during quit: {e}", exc_info=True)

        app.aboutToQuit.connect(on_about_to_quit)

        overlay.show()
        sys.exit(app.exec())
    
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"FATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
