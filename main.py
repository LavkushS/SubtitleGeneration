from flask import Flask, render_template, request
from flask import make_response,send_file
import torch
import whisper
import moviepy.editor as mp
from googletrans import Translator
from gtts import gTTS
import os
import shutil
from zipfile import ZipFile
# import logging
# logging.getLogger('werkzeug').disabled = True


app = Flask(__name__)

@app.route('/')
def home():
    response = make_response(render_template('index.html'))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/upload', methods=['POST'])
def upload():
    try:
        video = request.files['video']
        target_language = request.form['language']
        text_flag = 'text' in request.form
        translatedText_flag = 'translated_text' in request.form
        translatedAudio_flag = 'translated_audio' in request.form
        print(text_flag)
        print(translatedText_flag)
        print(translatedAudio_flag)
        print(target_language)
        # Save the uploaded video file
        video_path = 'uploaded_video.mp4'
        video.save(video_path)

        def convert_text_to_audio(text, language, filename):
            tts = gTTS(text=text, lang=language)
            tts.save(filename)

        def process_text_file(file_path):
            with open(file_path, 'r',encoding='utf-8') as file:
                content = file.read()
            # language = 'hi'
            convert_text_to_audio(content,target_language,'final_audio.mp3')
            print("success")

        def extract_audio(video_file, audio_file):
            clip = mp.VideoFileClip(video_file)
            audio = clip.audio
            audio.write_audiofile(audio_file)

        def transcribe_audio(audio_file, model_name):
            device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load the Whisper model
            model = whisper.load_model(model_name, device=device)

            # Transcribe the audio
            result = model.transcribe(audio_file)

            # Return the transcribed text
            return result["text"]

        def save_subtitles(subtitle_file, text):
            with open(subtitle_file, 'w',encoding='utf-8') as file:
                file.write(text)

        def convert_to_subtitle_format(text):
            lines = text.strip().split('\n')
            subtitles = []
            for i, line in enumerate(lines, start=1):
                start_time = (i - 1) * 5  # Adjust the duration between each subtitle as needed
                end_time = i * 5  # Adjust the duration between each subtitle as needed
                subtitle = f"{i}\n{start_time} --> {end_time}\n{line}\n\n"
                subtitles.append(subtitle)
            return '\n'.join(subtitles)

        def translate_text(text, target_language):
            translator = Translator()
            translation = translator.translate(text, dest=target_language)
            return translation.text
        
        audio_file = "audio.mp3"  # Output audio file path
        model_name = "tiny"  # Model name (e.g., "medium", "large")
        text_file = "text.txt"  # Output text file path
        subtitle_file = "subtitles.srt"  # Output subtitle file path
        translated_file = "translated.txt"  # storing the subtitle of another language

        extract_audio(video_path, audio_file)
        # Transcribe the audio
        text = transcribe_audio(audio_file, model_name)

        # Translate the text to the target language
        translated_text = translate_text(text, target_language)

        # Save the subtitles in hindi to a file
        save_subtitles(translated_file, translated_text)

        # Save the text file
        save_subtitles(text_file, text)

        ########convert the text to audio
        text_file_path = 'translated.txt'
        process_text_file(text_file_path)

        # Convert the text to subtitle format
        # subtitle_text = convert_to_subtitle_format(text)
        # Save the subtitles to a file
        # save_subtitles(subtitle_file, subtitle_text)

        print("Subtitles generated successfully.")

        try:
            # Create a temporary directory to store the files
            temp_dir = 'temp'
            os.makedirs(temp_dir, exist_ok=True)

            # Create a ZipFile Object
            zip_path = 'download_files.zip'
            with ZipFile(zip_path, 'w') as zip_object:
                # Adding files that need to be zipped
                if text_flag==True:
                    zip_object.write('text.txt')
                if  translatedText_flag==True:
                    zip_object.write('translated.txt')
                if translatedAudio_flag==True:
                    zip_object.write('final_audio.mp3')

            # Send the ZIP archive as an attachment
            return send_file(
                zip_path,
                as_attachment=True,
                download_name='download_files.zip',
                mimetype='application/zip'
            )
        except Exception as e:
            # Handle the exception gracefully (e.g., log the error, display an error message)
            return f"An error occurred: {str(e)}"
    except Exception as e:
        # Handle the exception gracefully (e.g., log the error, display an error message)
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)