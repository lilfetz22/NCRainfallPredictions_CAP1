FROM python:3

WORKDIR /usr/src/rainfall-predictor

## Install Dependencies
COPY requirements.txt .
COPY dockerconfig/install_IntelMKL.sh ./config/

# Special Library installation & cleanup
RUN [ "/bin/bash", "-c", "chmod +x ./config/install_IntelMKL.sh && ./config/install_IntelMKL.sh" ]

RUN pip install --no-cache-dir -r requirements.txt
# Secondary Dependencies 
RUN pip install https://github.com/IntelPython/mkl_fft/archive/v1.0.14.zip \
				https://github.com/IntelPython/mkl_random/archive/v1.0.2.zip \
				https://github.com/IntelPython/mkl-service/archive/v2.0.2.zip

## Copy Application Code
COPY dockerconfig/* ./config/
COPY build/* ./
COPY data/* ./data/
COPY src/main.py ./
# Enable script to execute & add entry into /usr/bin for app start
RUN chmod +x ./main.py
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
	&& ./config/configure_admin.sh "./config/.admin.secret"

## Delete configuration scripts & files
RUN rm -rf ./config

## Lock root account
RUN passwd --delete --lock root

## Run as daemon user
USER rainfalld
WORKDIR /var/cache/rainfall-predictor
CMD [ "python", "/usr/bin/rainfall-predictor" ]

