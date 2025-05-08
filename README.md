Guía de Instalación del Proyecto: Extracción de Información de Facturas
Requisitos Previos:
- Python 3.9 o superior
- Git
- Tesseract OCR

Descarga de Tesseract OCR
- Link descarga: https://sourceforge.net/projects/tesseract-ocr.mirror/postdownload
- Una vez descargado el archivo .exe sigue los siguientes pasos:
- Al momento de llegar al paso de elegir la ruta de instalación, dar click en "examinar", luego dar click en "Este equipo", luego elegir "Disco local C",
  estando allí creamos una carpeta la cual se tiene que llamar "Tesseract", por ultimo elegimos esa carpeta para finalizar la instalación.

Una vez clonado el repositorio, ingresar a la carpeta del proyecto
- cd Extracci-nFacturas

Luego abrimos una terminal en nuestro proyecto y ejecutamos el siguiente comando:
- pip install -r requirements.txt

Ejecutar en la misma terminal el siguiente comando para correr la aplicación
- python app.py
- Al correrlo nos dará un enlace local para poder ver nuestra aplicación la cual debemos abrirla en un navegador.
- Ejemplo: "http://127.0.0.1:5000"
  
