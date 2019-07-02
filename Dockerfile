FROM poldracklab/fmriprep:latest

WORKDIR /home/fpetprep
ENV HOME = "/home/fpetprep"
COPY . /fpetprep

RUN useradd -m -s /bin/bash -G users fpetprep


# Install ITK Python, C++,library debugging symbols headers wrapping from the ITK Software Guide
RUN sudo apt-get install -y --no-install-recommends\
                         cmake pkg-config

#install PETPVC
RUN cd /usr/local \
    git clone https://github.com/ucl/PETPVC.git \
    cd PETPVC \
    mkdir BUILD && cd BUILD \
    cmake /usr/local/PETPVC \
    make && make test \
    make install

#install dcm2niix, simpleitk, nilearn, pydicom
RUN conda install -c simpleitk simpleitk \
                 simpleitk/label/dev simpleitk \
                 conda-forge dcm2niix \
                 conda-forge nilearn \
                 conda-forge pydicom


#install GIFT
RUN wget http://mialab.mrn.org/software/gift/software/stand_alone/GroupICATv4.0b_standalone_Linux_x86_64.zip \
    sudo unzip GroupICATv4.0b_standalone_Linux_x86_64.zip -d /usr/local/GIFT \
    sudo rm -rf GroupICATv4.0b_standalone_Linux_x86_64.zip
    sudo unzip /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip -d /usr/local/MATLAB \
    sudo rm -rf /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip
# install MCR
    cd /usr/local/MATLAB \
    ./install -mode silent -agreeToLicense yes -destinationFolder /usr/local/MATLAB \

#install customized version of nipype
# TODO: move the required files to fpetprep directory and then copy to nipype directory
RUN cd /usr/local \
    git clone https://github.com/nipy/nipype.git \
    cp /fpetprep/nipype/interface/gift/* nipype/nipype/interfaces/gift \
    pip install -e /usr/local/nipype-0.10.0


ENTRYPOINT ["python", "parser.py"]





