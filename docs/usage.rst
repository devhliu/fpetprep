Usage
========

Example command to run fpetprep docker (with fpetprep docker wrapper)

	$fpetprepDocker /path/to/root/bids/dir --dicom_directort /path/to/dicom/directory ...

With docker command directly
	
	$docker run -v /path/to/data:/path/to/data/in/the/container fpetprep:latest arg1 arg2 ...