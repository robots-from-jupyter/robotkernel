FROM alpine:edge
MAINTAINER Asko Soukka <asko.soukka@iki.fi>

RUN apk add python3 build-base python3-dev jpeg-dev zlib-dev

# Install Jupyter
RUN mkdir -p /opt/jupyter
RUN python3 -m venv /opt/jupyter
RUN /opt/jupyter/bin/pip install -U setuptools pip
RUN /opt/jupyter/bin/pip install jupyter Pillow robotframework robotframework-archivelibrary robotframework-faker robotframework-seleniumlibrary robotframework-selenium2library robotframework-selenium2screenshots robotframework-webpack RESTinstance

# Install Geckodriver
RUN python3 -c "from urllib.request import urlretrieve; urlretrieve('https://github.com/mozilla/geckodriver/releases/download/v0.22.0/geckodriver-v0.22.0-linux64.tar.gz', 'geckodriver.tar.gz')"
RUN tar -xzf geckodriver.tar.gz -C /opt/jupyter/bin

# Install Robotkernel
RUN mkdir -p /var/src/robotkernel
ADD setup.py /var/src/robotkernel
ADD setup.cfg /var/src/robotkernel
ADD src /var/src/robotkernel/src
RUN /opt/jupyter/bin/pip install /var/src/robotkernel
RUN /opt/jupyter/bin/python -m robotkernel.install


FROM alpine:edge

RUN echo http://nl.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories
RUN apk --no-cache add firefox python3 tini ttf-dejavu

COPY --from=0 /opt /opt
COPY --from=0 /usr/local/share/jupyter /usr/local/share/jupyter

RUN mkdir -p /tmp/.jupyter
RUN echo "import os; c.NotebookApp.ip = os.environ.get('JUPYTER_NOTEBOOK_IP', '0.0.0.0')" > /tmp/.jupyter/jupyter_notebook_config.py

ADD example.ipynb /tmp
RUN chmod a+w /tmp/example.ipynb

ENV PATH="/opt/jupyter/bin:${PATH}"
ENV HOME=/tmp
WORKDIR /tmp
USER nobody

EXPOSE 8888

ENTRYPOINT ["tini", "--", "jupyter", "notebook"]
