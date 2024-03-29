FROM --platform=linux/amd64 python:3.10-bullseye
WORKDIR /code

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17

RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --skip-lock
COPY ./ .
ENTRYPOINT ["pipenv", "run", "python", "main.py"]
