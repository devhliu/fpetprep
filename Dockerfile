FROM poldracklab/fmriprep:latest

COPY . /fpetprep

RUN useradd -m -s /bin/bash -G users fpetprep
WORKDIR /home/fpetprep
ENV HOME = "/home/fpetprep"

# Install ITK Python, C++,library debugging symbols headers wrapping from the ITK Software Guide
RUN sudo apt-get install -y --no-install-recommends\
                         cmake pkg-config

#install PETPVC
RUN cd /usr/local
RUN git clone https://github.com/ucl/PETPVC.git
RUN cd PETPVC
RUN mkdir BUILD && cd BUILD
RUN cmake /usr/local/PETPVC
RUN make && make test
RUN make install

#install dcm2niix and simpleitk
conda install -c simpleitk simpleitk \
                 simpleitk/label/dev simpleitk \
                 conda-forge dcm2niix


#install GIFT
RUN wget http://mialab.mrn.org/software/gift/software/stand_alone/GroupICATv4.0b_standalone_Linux_x86_64.zip
RUN sudo unzip GroupICATv4.0b_standalone_Linux_x86_64.zip -d /usr/local/GIFT
RUN sudo unzip /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip -d /usr/local/MATLAB
# install MCR
RUN cd /usr/local/MATLAB
RUN ./install -mode silent -agreeToLicense yes -destinationFolder /usr/local/MATLAB

#install customized version of nipype
# TODO: move the required files to fpetprep directory and then copy to nipype directory
RUN cd /usr/local
RUN git clone https://github.com/nipy/nipype.git
RUN cp /fpetprep/nipype/interface/gift/* nipype/nipype/interfaces/gift
RUN pip install -e /usr/local/nipype-0.10.0

# install python packages: nilearn, pydicom
RUN pip install nilearn \
                pydicom --user







