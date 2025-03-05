from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QGraphicsView, QGraphicsScene)
from PySide6.QtCore import Qt, QTimer, QRectF, QByteArray
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath
from PySide6.QtMultimedia import QAudioFormat, QMediaDevices, QAudioSource
import pygame
import numpy as np
from array import array
import wave
import os
from datetime import datetime

class WaveformView(QGraphicsView):
    def __init__(self, wav_file, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setFixedWidth(200)
        self.setStyleSheet("background: transparent; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scene = QGraphicsScene(self)
        self.setScene(scene)
        
        # Generate waveform data
        self.generate_waveform(wav_file)
        self.draw_waveform()

    def generate_waveform(self, wav_file):
        try:
            with wave.open(wav_file, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                samples = array('h', frames)
                self.waveform = np.array(samples[::100])  # Reduce sample rate
                self.waveform = np.clip(self.waveform / max(abs(self.waveform)), -1, 1)
        except Exception as e:
            print(f"Error generating waveform: {e}")
            self.waveform = np.zeros(100)

    def draw_waveform(self):
        scene = self.scene()
        scene.clear()
        
        width = self.width()
        height = self.height()
        samples = len(self.waveform)
        
        path = QPainterPath()
        x_scale = width / samples
        
        for i, value in enumerate(self.waveform):
            x = i * x_scale
            y = height/2 + value * (height/2 - 5)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        pen = QPen(QColor("#ffffff"))
        pen.setWidth(2)
        scene.addPath(path, pen)

class VoiceMessageBubble(QFrame):
    def __init__(self, sender, file_path, timestamp, theme="Ночная", is_mine=False, reply_to=None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.file_path = file_path
        self.timestamp = timestamp
        self.theme = theme
        self.is_mine = is_mine
        self.reply_to = reply_to
        self.is_playing = False
        self.playback_speed = 1.0
        
        # Initialize pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        try:
            self.sound = pygame.mixer.Sound(self.file_path)
            self.duration = round(self.sound.get_length())
            self.current_position = 0
            self.can_play = True
        except Exception as e:
            print(f"Ошибка загрузки аудио: {e}")
            self.can_play = False
            self.duration = 0
            
        self.setup_ui()
        self.apply_theme()
        
        # Timer for updating play state and position
        self.play_timer = QTimer(self)
        self.play_timer.setInterval(100)
        self.play_timer.timeout.connect(self.update_playback)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Main container
        container = QFrame(self)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(4)
        
        if not self.is_mine:
            sender_label = QLabel(self.sender)
            sender_label.setStyleSheet("font-weight: bold;")
            container_layout.addWidget(sender_label)

        # Player controls container
        controls = QHBoxLayout()
        controls.setSpacing(8)
        
        # Play button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(36, 36)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setEnabled(self.can_play)
        controls.addWidget(self.play_button)
        
        # Waveform and progress
        waveform_container = QFrame()
        waveform_layout = QVBoxLayout(waveform_container)
        waveform_layout.setContentsMargins(0, 0, 0, 0)
        waveform_layout.setSpacing(2)
        
        # Waveform visualization
        self.waveform = WaveformView(self.file_path, self)
        waveform_layout.addWidget(self.waveform)
        
        # Time and speed controls
        time_speed = QHBoxLayout()
        
        # Current time / Duration
        self.time_label = QLabel(self.format_time(0) + " / " + self.format_time(self.duration))
        time_speed.addWidget(self.time_label)
        
        time_speed.addStretch()
        
        # Speed button
        self.speed_button = QPushButton("1x")
        self.speed_button.setFixedHeight(20)
        self.speed_button.clicked.connect(self.toggle_speed)
        time_speed.addWidget(self.speed_button)
        
        waveform_layout.addLayout(time_speed)
        controls.addWidget(waveform_container, 1)
        
        container_layout.addLayout(controls)
        
        # Timestamp
        time_label = QLabel(self.timestamp)
        time_label.setStyleSheet("color: #888; font-size: 10px;")
        container_layout.addWidget(time_label, 0, Qt.AlignRight)
        
        layout.addWidget(container)

    def format_time(self, seconds):
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes}:{seconds:02d}"

    def toggle_speed(self):
        speeds = [1.0, 1.5, 2.0]
        current_index = speeds.index(self.playback_speed)
        self.playback_speed = speeds[(current_index + 1) % len(speeds)]
        self.speed_button.setText(f"{self.playback_speed}x")
        
        if self.is_playing:
            # Restart playback with new speed
            self.toggle_playback()
            self.toggle_playback()

    def update_playback(self):
        if self.is_playing:
            self.current_position = min(self.current_position + 0.1, self.duration)
            self.time_label.setText(
                f"{self.format_time(self.current_position)} / {self.format_time(self.duration)}"
            )
            
            if self.current_position >= self.duration:
                self.stop_playback()

    def toggle_playback(self):
        if not self.can_play:
            return
            
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        pygame.mixer.stop()
        self.sound.play()
        self.is_playing = True
        self.play_button.setText("⏸")
        self.play_timer.start()

    def stop_playback(self):
        pygame.mixer.stop()
        self.is_playing = False
        self.play_button.setText("▶")
        self.play_timer.stop()
        self.current_position = 0
        self.time_label.setText(f"{self.format_time(0)} / {self.format_time(self.duration)}")

    def apply_theme(self):
        from themes import DARK_THEME, LIGHT_THEME
        theme = DARK_THEME if self.theme == "Ночная" else LIGHT_THEME
        
        bg_color = theme['bubble_mine'] if self.is_mine else theme['bubble_other']
        text_color = theme['bubble_text']
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {text_color};
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                color: {text_color};
                border-radius: 18px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:disabled {{
                background-color: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.3);
            }}
            #speed_button {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
            }}
        """)

class VoiceRecorder(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Store reference to parent window
        try:
            # Setup audio format
            self.format = QAudioFormat()
            self.format.setSampleRate(44100)
            self.format.setChannelCount(1)
            self.format.setSampleFormat(QAudioFormat.Int16)
            
            # Get default audio input device
            self.audio_input = QMediaDevices.defaultAudioInput()
            if not self.audio_input:
                raise Exception("No audio input device found")
            
            # Create audio source
            self.audio_source = QAudioSource(self.audio_input, self.format, self)
            self.is_recording = False
            self.audio_buffer = QByteArray()
            self.setup_ui()
            
        except Exception as e:
            print(f"Ошибка инициализации записи: {e}")
            self.audio_source = None
            self.setup_ui(False)

    def setup_ui(self, recording_available=True):
        self.record_btn = QPushButton("🎤")
        self.record_btn.setStyleSheet(
            "background-color: red; color: white; font-size: 18px; border-radius: 10px;"
        )
        if recording_available:
            self.record_btn.clicked.connect(self.toggle_voice_recording)
        else:
            self.record_btn.setEnabled(False)
            self.record_btn.setToolTip("Запись голоса недоступна")
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.record_btn)
        self.setLayout(layout)

    def toggle_voice_recording(self):
        if not self.audio_source:
            return

        if self.is_recording:
            # Stop recording
            self.audio_source.stop()
            self.is_recording = False
            self.record_btn.setText("🎤")
            
            # Save recorded audio
            try:
                save_path = os.path.join(os.getcwd(), "downloads")
                os.makedirs(save_path, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.output_file = os.path.join(save_path, f"voice_{timestamp}.wav")
                
                # Save as WAV file
                with wave.open(self.output_file, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(44100)
                    wav_file.writeframes(self.audio_buffer.data())
                
                print(f"Голосовое сообщение сохранено: {self.output_file}")
                
                # Send the voice message using parent reference
                if hasattr(self.parent_window, 'send_voice_message'):
                    self.parent_window.send_voice_message(self.output_file)
                else:
                    print("Ошибка: не найден метод отправки голосового сообщения")
                    print(f"Доступные методы: {dir(self.parent_window)}")
                    
            except Exception as e:
                print(f"Ошибка сохранения записи: {e}")
            
            self.audio_buffer.clear()
            
        else:
            # Start recording
            try:
                self.audio_buffer.clear()
                audio_device = self.audio_source.start()
                if audio_device:
                    audio_device.readyRead.connect(
                        lambda: self.audio_buffer.append(audio_device.readAll())
                    )
                    self.is_recording = True
                    self.record_btn.setText("⏹")
                    print("Запись началась...")
            except Exception as e:
                print(f"Ошибка начала записи: {e}")
                self.is_recording = False
                self.record_btn.setText("🎤")