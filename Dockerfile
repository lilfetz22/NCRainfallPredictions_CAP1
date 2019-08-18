FROM python:3

WORKDIR /usr/src/app

## Install Dependencies
COPY src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

## Copy Application Code
COPY build/* .
COPY src/main.py .
WORKDIR /usr/src/app/data
COPY data/*.csv .

# Build User
USER rainfalld

## Run
CMD [ "python", "/usr/src/app/main.py" ]
