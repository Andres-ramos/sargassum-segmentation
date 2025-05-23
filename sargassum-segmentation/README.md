# sargassum-segmentation

In this project we test the performance of a pretrained segmentation model in the task of nearshore sargassum semantic segmentation. The project cosists of two parts:

1. A segmentation dataset creation pipeline - This code can be found in the src/make_dataset.py file. It uses sargassum annotations obtained manually. It leverages guaraguao (https://github.com/Andres-ramos/guaraguao), a package I developed a while back to abstract the management and download of satellite images. This package is used to download the satellite images that are used for the project. 

2. A jupyter notebook that evaluates the performance of a pretrained segmentation model using the created dataset - This code can be found in the notebooks/segmentation.ipynb file

In order to run the jupyter notebook create an environment with python 3.11 using the following commands:

`python -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.py`

In order to run the notebook locally, download the data from this link (https://drive.google.com/file/d/1XVcvz51BkV20pSZCRN5aqjOwvb7Jq_Z0/view?usp=share_link) and past the folder in the /sargassum-segmentation folder, parallel to src/ and notebooks/. 

Although it is recommended you donwload the data to run the notebook, if you wish to run the dataset creation pipeline more set up is required. The dataset creation pipeline relies on guaraguao and this package is not very user friendly and has not been maintained. The reccomended way of installing guaraguao is to `git clone https://github.com/Andres-ramos/guaraguao` the packge into a sibling directory, `cd guaraguao/` into the package and run `pip install . `

This is not the only step required as you now need to create a google cloud token to be able to use the package. The instructions are in the project github. 