FROM poldracklab/fmriprep:latest

WORKDIR /home/fpetprep
ENV HOME = "/home/fpetprep"
COPY . /fpetprep

#RUN useradd -m -s /bin/bash -G users fpetprep


# Install ITK Python, C++,library debugging symbols headers wrapping from the ITK Software Guide
RUN apt-get update && \
    apt-get install -y --no-install-recommends\
                         cmake pkg-config \
                         wget \
			 unzip

#install PETPVC
RUN cd /usr/local \
    git clone https://github.com/ucl/PETPVC.git \
    mkdir /usr/local/PETPVC/BUILD \
    cd /usr/local/PETPVC/BUILD \
    cmake /usr/local/PETPVC \
    make \
    make install

#install customized version of nipype; move the required files to fpetprep directory and then copy to nipype directory
RUN git clone https://github.com/nipy/nipype.git /usr/local/nipype\
    && cp -R /fpetprep/gift nipype/nipype/interfaces/gift/ \
    && pip install -e /usr/local/nipype

#install dcm2niix, simpleitk, nilearn, pydicom
RUN conda install -c simpleitk simpleitk \
    && conda install -c simpleitk/label/dev simpleitk \
    && conda install -c conda-forge dcm2niix \
    && conda install -c conda-forge pydicom \
    && conda install -c conda-forge nilearn \
    && pip install heudiconv



#install GIFT and MCR
RUN wget http://mialab.mrn.org/software/gift/software/stand_alone/GroupICATv4.0b_standalone_Linux_x86_64.zip \ 
    && unzip GroupICATv4.0b_standalone_Linux_x86_64.zip -d /usr/local/GIFT \ 
    && rm -rf GroupICATv4.0b_standalone_Linux_x86_64.zip \
    && unzip /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip -d /usr/local/MATLAB \
    && rm -rf /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip \
    && cd /usr/local/MATLAB \
    && ./install -mode silent -agreeToLicense yes -destinationFolder /usr/local/MATLAB \




ENTRYPOINT ["python", "parser.py"]





