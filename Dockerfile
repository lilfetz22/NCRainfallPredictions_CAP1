FROM python:3

WORKDIR /usr/src/rainfall-predictor

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
COPY config/* ./config/
COPY build/* ./
COPY data/* ./data/
COPY src/main.py ./
# Entry into /usr/bin for app start
RUN ln -s "${PWD}/main.py" /usr/bin/rainfall-predictor

## Build System Daemon (no-user-group, system daemon, set $HOME)
RUN useradd --system --no-user-group --gid daemon \
			--create-home --home-dir "/var/cache/rainfall-predictor" \
			rainfalld

## Create output log location
RUN mkdir -p "/var/log/rainfall-predictor" \
	&& chown rainfalld "/var/log/rainfall-predictor"

## Create Admin sudoer user
RUN apt-get install sudo
RUN useradd --user-group --groups sudo --create-home \
			--comment "Administrator" \
			admin

# set admin password
RUN chmod +x ./config/configure_admin.sh \
	&& ./config/configure_admin.sh "./config/.admin.secret" \
	&& rm ./config/configure_admin.sh

## Run as daemon user
USER rainfalld
WORKDIR /var/cache/rainfall-predictor
CMD [ "python", "/usr/bin/rainfall-predictor" ]

