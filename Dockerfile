FROM python:3

WORKDIR /usr/src/app

## Install Dependencies
COPY src/requirements.txt .
COPY config/install_IntelMKL.sh ./config/

# Special Library installation & cleanup
RUN [ "/bin/bash", "-c", "chmod +x ./config/install_IntelMKL.sh && ./config/install_IntelMKL.sh && rm ./config/install_IntelMKL.sh" ]

RUN pip install --no-cache-dir -r requirements.txt
# Secondary Dependencies 
RUN pip install https://github.com/IntelPython/mkl_fft/archive/v1.0.14.zip \
				https://github.com/IntelPython/mkl_random/archive/v1.0.2.zip \
				https://github.com/IntelPython/mkl-service/archive/v2.0.2.zip

## Copy Application Code
COPY build/* .
COPY src/main.py .
WORKDIR /usr/src/app/data
COPY data/*.csv .

## Build User
USER rainfalld

## Run
CMD [ "python", "/usr/src/app/main.py" ]
