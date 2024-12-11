import asyncio as aio
import tempfile
from io import BytesIO

import numpy as np
import sounddevice as sd
import soundfile as sf
from langchain_openai import ChatOpenAI
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from loguru import logger
from openai import OpenAI
from pydub import AudioSegment

from .chat.agent import TOOLS, Agent
from .config import config
from .utils.stopwatch import Stopwatch

agent_model = ChatOpenAI(model="gpt-4o", streaming=True, name="main")


class SilenceDetector:
    def __init__(self, samplerate, idle_timeout, min_volume):
        self.samplerate = samplerate
        self.idle_timeout = idle_timeout
        self.min_volume = min_volume
        self.silence_duration = 0
        self.silence_only = True

    def detect(self, indata):
        volume_norm = np.linalg.norm(indata) * 10

        if volume_norm < self.min_volume:
            self.silence_duration += len(indata) / self.samplerate
        else:
            self.silence_duration = 0
            self.silence_only = False

        # logger.debug(
        #     f"SilenceDuration: {self.silence_duration}; VolumeNorm: {volume_norm}"
        # )
        return self.has_silence_detected()

    def has_silence_detected(self):
        return self.silence_duration >= self.idle_timeout


class Microphone:
    def __init__(
        self, idle_timeout_seconds=2, min_volume=0.01, block_size=1024, samplerate=16000
    ):
        self.idle_timeout_seconds = idle_timeout_seconds
        self.min_volume = min_volume
        self.block_size = block_size
        self.samplerate = samplerate

    async def record(self):
        logger.info("Start recording...")
        recording = True

        audio_buffer = BytesIO()
        silence_detector = SilenceDetector(
            self.samplerate,
            self.idle_timeout_seconds,
            self.min_volume,
        )

        def callback(indata, frames, time, status):
            nonlocal silence_detector
            if status:
                print(f"Microphone error: {status}")

            if recording and not silence_detector.detect(indata):
                audio_chunk = (indata * 32767).astype(np.int16).tobytes()
                audio_buffer.write(audio_chunk)

        with sd.InputStream(
            callback=callback,
            blocksize=self.block_size,
            channels=1,
            samplerate=self.samplerate,
            dtype="float32",
        ):
            while recording:
                await aio.sleep(0.1)
                if silence_detector.has_silence_detected():
                    recording = False

        logger.info("Stop recording...")

        if silence_detector.silence_only:
            return None

        return self._save_recording(audio_buffer)

    def _save_recording(self, audio_buffer):
        audio_buffer.seek(0)
        raw_audio = AudioSegment(
            audio_buffer.read(),
            frame_rate=self.samplerate,
            sample_width=2,
            channels=1,
        )
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        raw_audio.export(tmp_file.name, format="mp3")
        return tmp_file.name


class Transcribe:
    def __init__(self, recording_path):
        self.client = wrap_openai(OpenAI())
        self.record_path = recording_path

    @traceable
    def transcribe(self):
        with open(self.record_path, "rb") as f:
            transcript = self.client.audio.transcriptions.create(
                file=f,
                model="whisper-1",
            )

        return transcript


class TranscriptFixer:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = wrap_openai(OpenAI())
        self.model = model
        self.system_prompt = "You are a helpful assistant. Your task is to correct any spelling discrepancies in the transcribed text. Convert time to 24h format, and dates to the YYYY-MM-DD format. Assume that the time is probably never in the night."

    @traceable
    def fix(self, transcript):
        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": transcript.text},
            ],
        )

        return res.choices[0].message.content


class TTS:
    def __init__(self, voice="alloy"):
        self.client = wrap_openai(OpenAI())
        self.voice = voice

    @traceable
    def convert(self, text):
        res = self.client.audio.speech.create(
            model="tts-1", voice=self.voice, input=text
        )
        res.write_to_file("response.mp3")
        return "response.mp3"


class AudioResponse:
    def __init__(self, audio_file: str):
        self.audio_file = audio_file

    def play(self):
        with sf.SoundFile(self.audio_file) as soundfile:
            logger.info(f"SampleRate: {soundfile.samplerate}")
            sd.play(soundfile.read(dtype="float32"), samplerate=soundfile.samplerate)
            sd.wait()


@traceable
async def main():
    agent = Agent(
        agent_model=agent_model,
        system_prompt="""You are a helpful telephone assistant.
Your task is to talk to the customer and create appointments for the user.
If the user has not provided you a date first ask him about the date and time he wants to have his appointment.
Then check whether his preffered slot is available. Only when a slot has been found continue.
Ask him about his name and phone number.
Then repeat it to him and let him fix it if there are mistakes.
Only now you are allowed to book an appointment.
Never ask the user to say something in a specific format, just tell him you didn't understand and ask again.
Todays date is 16.11.2024, if the user does not provide a year use 2024.
Reduce your output to a minimum it is important to save cost and time.
""",
        tools=TOOLS,
    )

    # Play some example audio here

    while True:
        recording_path = None
        while recording_path is None:
            mic = Microphone(min_volume=2.5)
            recording_path = await mic.record()
            logger.info(f"RecordingPath: {recording_path}")

        sw = Stopwatch()
        transcribe = Transcribe(recording_path)
        transcript = transcribe.transcribe()
        logger.info(f"Transcript: {transcript}, took: {sw()}")
        if transcript is None:
            continue

        # transcript_fixer = TranscriptFixer()
        # fixed_transcript = transcript_fixer.fix(transcript)
        # logger.info(f"FixedTranscript: {fixed_transcript}, took: {sw()}")
        # if fixed_transcript is None:
        #     continue

        agent_reply = ""
        async for chunk in agent.reply(transcript.text):
            agent_reply += chunk
        logger.info(f"AgentReply: {agent_reply}, took: {sw()}")

        tts = TTS()
        audio_response_file = tts.convert(agent_reply)
        logger.info(f"TTS: took: {sw()}")

        audio_response = AudioResponse(audio_response_file)
        audio_response.play()
        logger.info("Done playing...")


if __name__ == "__main__":
    aio.run(main())
