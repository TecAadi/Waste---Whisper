************************************************************
*******************  INSTRUCTION ***************************
************************************************************

Users can download the waste dataset directly and store them on their own machines.
Then further processing can be performed locally. This is the recommended option to
reduce processing time and avoid runtime disconnection on Google Colab.
However, you can use the Jupyter notebook (.ipynb) directly on Google Colab by performing the following steps:

1.	Run the "waste_dataset_augmentation.ipynb" first. 
	This will download, augment and save the image files on your Google Drive.
	
2.	Run the "waste_dataset_CNN.ipynd" file second.
	This will train the various models and produce test results afterwards