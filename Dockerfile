FROM node
RUN apt update
RUN apt-get install python3-pip -y
RUN apt-get install git
RUN git clone https://github.com/vasukivasan/WDC2.git
RUN cd WDC2
RUN ls
RUN pip install -r WDC2/requirements.txt --break-system-packages
RUN apt-get update && apt-get install libgl1 libsm6 libxext6  -y
CMD python3 WDC2/main.py

