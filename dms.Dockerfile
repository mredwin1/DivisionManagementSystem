FROM python:3.8.2-slim-buster

# Allow service to handle stops gracefully
STOPSIGNAL SIGQUIT

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_NOSPIN=1

# Install project dependencies
RUN pip install -U pipenv

# Copy the project files into working directory
COPY . .

# Install the dependencies
RUN pipenv install --system --deploy

# Run web server through custom manager
ENTRYPOINT ["python", "manage.py"]
CMD ["run"]