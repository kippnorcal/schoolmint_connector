FROM python:3
WORKDIR /code
RUN wget https://packages.microsoft.com/debian/9/prod/pool/main/m/msodbcsql17/msodbcsql17_17.2.0.1-1_amd64.deb 
RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y unixodbc unixodbc-dev
RUN pip install pipenv
COPY Pipfile .
RUN pipenv install --skip-lock
RUN yes | dpkg -i msodbcsql17_17.2.0.1-1_amd64.deb
COPY ./ .
CMD ["pipenv", "run", "python", "main.py"]
