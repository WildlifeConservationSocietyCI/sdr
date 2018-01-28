FROM sparkgeo/base:django3

RUN apt-get install -y --no-install-recommends \
    nano \
    less

ADD ./requirements.txt ./requirements.txt
#RUN rm /usr/local/bin/pip
#RUN ln -s /usr/local/bin/pip3.4 /usr/local/bin/pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN rm ./requirements.txt

WORKDIR /var/projects/webapp
ADD ./src .
RUN mkdir -p ./static
ADD ./config/webapp.nginxconf /etc/nginx/sites-enabled/

EXPOSE 80 443 8000
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
