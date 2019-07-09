#FROM poldracklab/fmriprep:latest

FROM ubuntu:xenial

# Prepare environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    curl \
                    bzip2 \
                    ca-certificates \
                    xvfb \
                    cython3 \
                    build-essential \
                    autoconf \
                    libtool \
                    pkg-config \
                    wget \
                    jq vim \
                    git && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#install neurodebian
RUN wget -O- http://neuro.debian.net/lists/xenial.us-tn.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

#install fsl
RUN apt-get update && apt-get install -y fsl

ENV FSLDIR=/usr/share/fsl/5.0
ENV PATH=$PATH:$FSLDIR/bin
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0:/usr/share/fsl/5.0/bin

#simulate . ${FSLDIR}/etc/fslconf/fsl.sh
ENV FSLBROWSER=/etc/alternatives/x-www-browser
ENV FSLCLUSTER_MAILOPTS=n
ENV FSLLOCKDIR=
ENV FSLMACHINELIST=
ENV FSLMULTIFILEQUIT=TRUE
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV FSLREMOTECALL=
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish
ENV POSSUMDIR=/usr/share/fsl/5.0


#install miniconda
RUN curl -sSLO https://repo.continuum.io/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh && \
    bash Miniconda3-4.5.11-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-4.5.11-Linux-x86_64.sh

ENV PATH="/usr/local/miniconda/bin:$PATH" \
    CPATH="/usr/local/miniconda/include/:$CPATH" \
    LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONNOUSERSITE=1

RUN conda install -y python=3.7.1 \
                     pip=19.1 \
                     mkl=2018.0.3 \
                     mkl-service \
                     numpy=1.15.4 \
                     scipy=1.1.0 \
                     scikit-learn=0.19.1 \
                     matplotlib=2.2.2 \
                     pandas=0.23.4 \
                     libxml2=2.9.8 \
                     libxslt=1.1.32 \
                     graphviz=2.40.1 \
                     traits=4.6.0 \
                     conda-build \
                     zlib; sync && \
    chmod -R a+rX /usr/local/miniconda; sync && \
    chmod +x /usr/local/miniconda/bin/*; sync && \
    conda build purge-all; sync && \
    conda clean -tipsy && sync

#install PETPVC
RUN cd /usr/local \
    git clone https://github.com/ucl/PETPVC.git \
    mkdir /usr/local/PETPVC/BUILD \
    cd /usr/local/PETPVC/BUILD \
    cmake /usr/local/PETPVC \
    make \
    make install

#install dcm2niix, simpleitk, nilearn, pydicom
RUN conda install -c simpleitk simpleitk \
    && conda install -c simpleitk/label/dev simpleitk \
    && conda install -c conda-forge dcm2niix \
    && conda install -c conda-forge pydicom \
    && conda install -c conda-forge nilearn \
    && conda build purge-all; sync \
    && conda clean -tipsy && sync \
    && pip install heudiconv


#install GIFT and MCR
RUN apt-get install unzip \
    && wget http://mialab.mrn.org/software/gift/software/stand_alone/GroupICATv4.0b_standalone_Linux_x86_64.zip \ 
    && unzip GroupICATv4.0b_standalone_Linux_x86_64.zip -d /usr/local/GIFT \ 
    && rm -rf GroupICATv4.0b_standalone_Linux_x86_64.zip \
    && unzip /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip -d /usr/local/MATLAB \
    && rm -rf /usr/local/GIFT/GroupICATv4.0b_standalone/MCRInstaller.zip \
    && cd /usr/local/MATLAB \
    && ./install -mode silent -agreeToLicense yes -destinationFolder /usr/local/MATLAB \
    && git clone https://github.com/nipy/nipype.git /usr/local/nipype

WORKDIR /home/fpetprep
ENV HOME = "/home/fpetprep"
COPY . /home/fpetprep

#RUN useradd -m -s /bin/bash -G users fpetprep           

#install customized version of nipype; move the required files to fpetprep directory and then copy to nipype directory
RUN cp -R //home/fpetprep/gift /usr/local/nipype/nipype/interfaces/gift/ \
    && pip install -e /usr/local/nipype

ENTRYPOINT ["python", "parser.py"]





