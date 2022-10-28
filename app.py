from http import server
from werkzeug.utils import secure_filename
from flask import Flask
import time
import requests
import json

import jyserver.Flask as jsf
from flask import render_template,request
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import azure.cognitiveservices.speech as speechsdk
import pyaudio
import wave
import os
from datetime import datetime



app = Flask(__name__)
app.config['AUDIO_FOLDER'] = "static/audios"
basedir = os.path.abspath(os.path.dirname(__file__))

# variables globales
enviado=False
enviar = {'idinvitacion': '',
          'encuestado':'',
          'encuesta':'',
          'fecha':'',
          'audio':'',
          'texto':''}





# poner archivo api.key en gitignore si se sube como (publico) a Github
file = "/api.key"
path = os.getcwd()+file
with open(path, 'r') as key:
    apiKey = key.read().replace('\n', '')
# llama a la api para saber la tecnologia activa
urlapi = 'https://surveys2t.herokuapp.com/techActive/'+apiKey
respuesta = requests.request("GET", urlapi)
dato = respuesta.json()
try:
  tecnologia = dato['tech_name']
  tecnologia_id = dato['tech_id']
  tecnologia_apikey = dato['tech_apiKey']
  tecnologia_zona = dato['tech_zona']
except:
  tecnologia = "Por defecto Google Speech"
  tecnologia_id = 1
 


grabar = True

@jsf.use(app)
class App:
    def __init__(self):
        pass

    def grabar(self):
      global enviado
      if not enviado:
        self.js.grabar.style.display = "none"
        self.js.guardarencuesta.style.display = "none"
        self.js.parar.style.display = "block"
        self.js.dom.time.style.display = "none"
        self.js.informacion.style.display = "none"
        self.js.playwav.style.display = "none"
        self.js.botontextowav.style.display = "none"
        self.js.mytextarea.style.display = "none"
        self.js.mytextarea.value = "Espere a que se procese el audio"
        self.js.dom.mensaje.innerHTML = "grabando.... Hable con naturalidad y haga los descansos necesarios"

        # DEFINIMOS PARAMETROS
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        # el audio se va a grabar con el nombre de identificador de la invitación
        global enviar
        archivo = enviar['audio']
        # INICIAMOS "pyaudio"
        audio = pyaudio.PyAudio()
        # INICIAMOS GRABACIÓN
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        frames = []
        start = time.time()
        minutosmaximopermitidos = 1
        global grabar
        while grabar:
            data = stream.read(1024)
            frames.append(data)
            duracion = time.time()-start
            segundos = duracion % 60
            minutos = duracion // 60
            horas = minutos // 60
            textotiempo = "Tiempo grabado " + \
                f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
            self.js.dom.time.innerHTML = textotiempo
            self.js.dom.parar.innerHTML = textotiempo + " pulse para Parar de grabar"
            if minutos >= minutosmaximopermitidos:
                grabar = False

        stream.stop_stream()
        stream.close()
        audio.terminate()
        grabar = True
        self.js.grabar.style.display = "block"
        self.js.dom.time.style.display = "block"
        self.js.parar.style.display = "none"
        self.js.informacion.style.display = "block"
        self.js.dom.mensaje.innerHTML = "terminado. Generando archivo wav"
        self.js.dom.grabar.style.color = 'white'
        self.js.dom.grabar.style.backgroundColor = 'blue'
      
        # CREAMOS/GUARDAMOS EL ARCHIVO DE AUDIO
        waveFile = wave.open(enviar['audio'], 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        self.js.playwav.style.display = "block"
        self.js.dom.mensaje.innerHTML = "Archivo (wav) almacenado en servidor local"
        self.js.botontextowav.style.display = "block"
        self.js.grabar.innerHTML = 'PULSE AQUI SI DESEA SUSTITUIR SU GRABACION POR OTRA'
        
        if minutos >= minutosmaximopermitidos:
            self.js.dom.mensaje.innerHTML = "Su tiempo se ha acabado"
        self.elegirtecnologia()   
      else:
         return App.render(render_template('terminado.html', respuesta="ya tenemos su grabación"))
    def playwav(self):
        global enviar
        sound = AudioSegment.from_wav(enviar['audio'])
        play(sound)

    def informacion(self):
        self.js.zonacontenido.style.display = "none"
        self.js.areainformacion.style.display = "block"
        self.js.botoncerrarinformacion.style.display = "block"
        self.js.informacion.style.display = "none"

    def cerrarinformacion(self):
        self.js.zonacontenido.style.display = "block"
        self.js.areainformacion.style.display = "none"
        self.js.botoncerrarinformacion.style.display = "none"
        self.js.informacion.style.display = "block"
    def cambiartexto(self):
        enviar['texto'] = str(self.js.mytextarea.value)
        
       
        
    def elegirtecnologia(self):
        global tecnologia_id
        self.js.mensaje.style.display = "none"
        # tener en cuenta si alguien cambia estos datos 
        # manipulando la tabla SQL fuera de las utilidades de back-end
        # el id(1) corresponde a a google speech
        # el id(2) corresponde a AssemblyAI
        # el id(3) corresponde a Azure
        
        # FALTA AÑADIR MAS TECNOLOGIAS POSIBLEMENTE CONTEMPLADAS EN LA API
        if tecnologia_id == 2:
            self.js.botontextowav.style.display = "none"
            self.js.mytextarea.style.display = "block"
            self.js.informacion.style.display = "none"
            self.js.mytextarea.value = "Espere a que se procese el audio de AssemblyAI"
            import assemblyai
            global tecnologia_apikey
            url_subida = self.subida()
            id_audio = self.transcripcion(url_subida)
            texto = self.resultado(id_audio)
            self.js.mytextarea.value = texto
            enviar['texto'] = texto
            self.js.guardarencuesta.style.display = "block"
            self.js.mejorartranscripcion.style.display = "block"
           
       
        elif tecnologia_id == 3:
            self.tecnologia_Azure()
        else:
            self.tecnologia_Recognizer()
       
   
     
    def subida(self):
        global enviar
        filename = enviar['audio']
        def read_file(filename, chunk_size=5242880):
          with open(filename, 'rb') as _file:
              while True:
                  data = _file.read(chunk_size)
                  if not data:
                      break
                  yield data

        headers = {'authorization': "7dfd52432dd14dd49e668a3416043b0c"}
        response = requests.post('https://api.assemblyai.com/v2/upload',
                                headers=headers,
                                data=read_file(filename))
        data = response.json()
        return(data["upload_url"])
    


    def transcripcion(self,url_subida):
          endpoint = "https://api.assemblyai.com/v2/transcript"

          json = {
          "audio_url": url_subida,
          "language_code": "es"
          }

          headers = {
          "authorization": "7dfd52432dd14dd49e668a3416043b0c",
          "content-Type": "application/json"
          }

          response = requests.post(endpoint, json=json, headers=headers)
          data = response.json()
          return(data['id'])


    def resultado(self,id_audio):

          endpoint = f"https://api.assemblyai.com/v2/transcript/{id_audio}"

          headers = {
          "Authorization": "7dfd52432dd14dd49e668a3416043b0c"
          }
          time.sleep(5)
          var=None
          while var!='error' and var!='completed':
              response = requests.get(endpoint, headers=headers)
              data = response.json()
              var = data['status']
          return (data['text'])
        
     
      
        
    def tecnologia_AssemblyAi(self):
        global tecnologia_apikey
        languaje="es"
        self.js.botontextowav.style.display = "none"
        self.js.mytextarea.style.display = "block"
        self.js.informacion.style.display = "none"
        self.js.mytextarea.value = "Espere a que se procese el audio de AssemblyAI"
        upload_endpoint = 'https://api.assemblyai.com/v2/upload'
        transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
        headers_auth_only = {'authorization': tecnologia_apikey}
        headers = {
        "authorization": tecnologia_apikey,
        "content-type": "application/json"
        }
        global enviar
        filename=enviar['audio']
        title="texto_grabado"
        CHUNK_SIZE = 5_242_880  # 5MB
        def upload(filename):
          def read_file(filename):
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break
                    yield data

          upload_response = requests.post(upload_endpoint, headers=headers_auth_only, data=read_file(filename))
          return upload_response.json()['upload_url']
            
        
        
        
        def transcribe(audio_url):
          transcript_request = {
            'audio_url': audio_url,
            'languaje_detection':True
        }
          transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
          return transcript_response.json()["id"]

        def poll(transcript_id):
          polling_endpoint = transcript_endpoint + '/' + transcript_id
          polling_response = requests.get(polling_endpoint, headers=headers)
          return polling_response.json() 
        

       
        
        def get_transcription_result_url(url):
          transcribe_id = transcribe(url)
          while True:
              data = poll(transcribe_id)
              if data['status'] == 'completed':
                  return data, None
              elif data['status'] == 'error':
                  return data, data['error']
                  
              print("waiting for 30 seconds")
              time.sleep(30)
            
        def save_transcript(url, title):
          data, error = get_transcription_result_url(url)
        
          if data:
              filename = title + '.txt'
              with open(filename, 'w') as f:
                  f.write(data['text'])
              print('Transcript saved')
              self.js.mytextarea.value = data['text']
              global enviar
              enviar['texto'] = data['text']
             
             
          elif error:
              print("Error!!!", error)
          else:
            time.sleep(30)    

        
        audio_url = upload(filename)
        save_transcript(audio_url,title)
            
            
            
    def tecnologia_Azure(self):
        self.js.botontextowav.style.display = "none"
        self.js.mytextarea.style.display = "block"
        self.js.informacion.style.display = "none"
        self.js.mytextarea.value = "Espere a que se procese el audio. Azure tarda más tiempo"
        global tecnologia_apikey
        global tecnologia_zona
        global enviar
        speech_key, service_region = tecnologia_apikey, tecnologia_zona
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=service_region)
        speech_config.speech_recognition_language = "es-ES"
        audio_config = speechsdk.audio.AudioConfig(filename=enviar['audio'])
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config)
        done = False

        def stop_cb(evt):
            """callback that stops continuous recognition upon receiving an event `evt`"""
            print('CLOSING on {}'.format(evt))
            speech_recognizer.stop_continuous_recognition()
            nonlocal done
            done = True

        all_results = []

        def handle_final_result(evt):
            all_results.append(evt.result.text)

        speech_recognizer.recognized.connect(handle_final_result)
        # Connect callbacks to the events fired by the speech recognizer
        speech_recognizer.recognizing.connect(
            lambda evt: print('RECOGNIZING: {}'.format(evt)))
        speech_recognizer.recognized.connect(
            lambda evt: print('RECOGNIZED: {}'.format(evt)))
        speech_recognizer.session_started.connect(
            lambda evt: print('SESSION STARTED: {}'.format(evt)))
        speech_recognizer.session_stopped.connect(
            lambda evt: print('SESSION STOPPED {}'.format(evt)))
        speech_recognizer.canceled.connect(
            lambda evt: print('CANCELED {}'.format(evt)))
        # stop continuous recognition on either session stopped or canceled events
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(.5)

        self.js.mytextarea.value = all_results
        self.js.guardarencuesta.style.display = "block"
        self.js.mejorartranscripcion.style.display = "block"
        enviar['texto'] = all_results
        
       

    def tecnologia_Recognizer(self):
        global enviar
        speech = sr.Recognizer()
        self.js.botontextowav.style.display = "none"
        self.js.mytextarea.style.display = "block"
        self.js.informacion.style.display = "none"
        with sr.AudioFile(enviar['audio']) as source:
            speech.adjust_for_ambient_noise(source)
            recorded_audio = speech.listen(source)
            try:
                text = speech.recognize_google(
                    recorded_audio,
                    language="es-ES"
                )
                self.js.guardarencuesta.style.display = "block"
                self.js.mejorartranscripcion.style.display="block"
            except Exception as ex:
                self.js.mytextarea.value = "ha ocurrido un error. Posiblemente el archivo quedó en blanco. Esta grabación no se ha procesado.Por favor, repita su grabación. si continua teniendo problemas consulte con su encuestador."
                self.js.guardarencuesta.style.display = "none"
               
        self.js.mytextarea.value = text
        enviar['texto']=text
        
       

    def pararspeech(self):
        global grabar
        grabar = False
       


@app.context_processor
def context_processor():
    return dict(
        tituloH1="Reto automatización de encuestas ",
        tituloH2="Mr Houston Python-Talento Digital ",

    )

# se iran añadiendo o quitando estas posibilidades segun diseñemos la url invitación


@app.route("/")
@app.route("/<string:identificador>")

def index(identificador=None):
    # ejemplo de comprobación de parametros de invitación (faltaría validación)
    if identificador :
        global grabar
        grabar=True
        global enviado
        enviado=False
        global enviar
        enviar['idinvitacion']=identificador
        enviar['audio']=os.path.join(basedir, app.config['AUDIO_FOLDER'],identificador+".wav")
        # llama a la api para sacar datos de la invitacion
        urlapi = 'https://surveys2t.herokuapp.com/comprobarinvitacion/'+apiKey+"/"+identificador
        respuesta = requests.request("GET", urlapi)
        dato = respuesta.json()
        try:
          encuestado_id = dato['encuestado_id']
          enviar['encuestado']=encuestado_id
          encuesta_id = dato['encuesta_id']
          enviar['encuesta']=encuesta_id
          fecha_invitacion = dato['fecha_invitacion']
          # llama a la api para sacar datos de la encuesta
          urlapi = 'https://surveys2t.herokuapp.com/datosDeEncuesta/' + \
              apiKey+"/" + str(encuesta_id)
          respuesta = requests.request("GET", urlapi)
          datoencuesta = respuesta.json()
          encuestador_id = datoencuesta['encuestador_id']
          fecha_inicio = datoencuesta['fecha_inicio']
          fecha_fin = datoencuesta['fecha_fin']
          encuesta_nombre = datoencuesta['encuesta_nombre']
          encuesta_pregunta = datoencuesta['encuesta_pregunta']
          encuesta_observaciones = datoencuesta['encuesta_observaciones']
          # llama a la api para sacar datos del encuestador
          urlapi = 'https://surveys2t.herokuapp.com/datosDeEncuestador/' + \
              apiKey+"/" + str(encuestador_id)
          respuesta = requests.request("GET", urlapi)
          datoencuestador = respuesta.json()
          encuestador_nombre = datoencuestador['encuestador_nombre']
          encuestador_logo = datoencuestador['encuestador_logo']
          # llama a la api para sacar datos del encuestado
          urlapi = 'https://surveys2t.herokuapp.com/datosDeEncuestado/'+apiKey+"/" + str( encuestado_id)
          respuesta = requests.request("GET", urlapi)
          datoencuestado = respuesta.json()
          encuestado_mail = datoencuestado['encuestado_mail']
          encuestado_wp = datoencuestado['encuestado_wp']
          encuestado_departamento = datoencuestado['encuestado_departamento']
          nombrearchivodeaudio = identificador+".wav"
          urlapi = 'https://surveys2t.herokuapp.com/comprobarrespuesta/' + \
              apiKey+"/" + nombrearchivodeaudio
          respuesta = requests.request("GET", urlapi)
          datorespuesta = respuesta.json()
          if datorespuesta:
             return App.render(render_template('info.html',mensaje="Esta invitación ya ha sido respondida"))
          else: 
            return App.render(render_template('index.html', mail=encuestado_mail,identificador=identificador,encuestador=encuestador_nombre,encuesta=encuesta_nombre, pregunta=encuesta_pregunta, tecnologia=tecnologia))
              
        except:
          return App.render(render_template('info.html',mensaje="error"))
       
    else:
        return App.render(render_template('info.html'))




@app.route("/terminado")
def terminado():
  respuestahtml = ""
  global enviar
  global enviado
  if not enviado:
      datehoy = datetime.now()
      dateStr = datehoy.strftime("%Y/%m/%d")
      enviar['fecha'] = dateStr
      enviar['audio']=enviar['idinvitacion']+".wav"
      file = "/api.key"
      path = os.getcwd()+file
      with open(path, 'r') as key:
        apiKey = key.read().replace('\n', '')
      

      cabecera = {'Content-type': 'application/json', 'Accept': 'text/plain'}
      response = requests.post(
          'https://surveys2t.herokuapp.com/respuesta', json=enviar, headers=cabecera)
      if response.ok:
          respuestahtml=".ok enviado"
          enviado=True
      else:
          respuestahtml=".no se puedo enviar"  
  if respuestahtml=="":   respuesta=".ok enviado"        
  return App.render(render_template('terminado.html',respuesta=respuestahtml))


# front-end ejecuta en servidor web local(localhost) en puerto 5000
# he designado el puerto 8000 para tener en ejecución el back-end(api) al mismo tiempo
# y poder hacer fetch para ver que tecnología es "active" y redirigir
# la transcripción de texto a la función que corresponda.
if __name__ == '__main__':
    app.run(5000)
# el modo depuracion (debug) te permite observar los cambios en tiempo real en en navegador
