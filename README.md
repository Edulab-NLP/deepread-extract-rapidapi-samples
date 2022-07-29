DEEPREAD Extract - AI OCR - RapidAPI Samples
=============

This repository provides an example Python script along with some sample images to test the DEEPREAD Extract - AI OCR
RapidAPI endpoints.

Installation
----------
The easiest way to run samples is within a virtual environment using Python3.

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
``` 

Once all the requirements are installed the samples can be processed.

Command line args
-----------
Required params:

`-k`|`--key`: `X-RapidAPI-Key` header required to access rapidapi.

One of these are required:

`--all`: when selected, all images in `samples/` folder will be process.

`-f`|`--file`: to specify a specific file you want to process.

Required for English analysis when specifying individual file:

`-p`|`--process-type`: to specify a process type for analysis. in set (form, invoice, receipt).

Other args:

`--vis`: when selected, a visualisation output will be created.

`-l`|`--language`: ACCEPT-LANGUAGE value passed to rapidapi/deepread. (default `en`)

`-h`|`--help`: output details of command line inputs.

Usage
----------
To process a specific image (notice how process-type argument is required):
`python run_extract_samples.py -k <X-RapidAPI-Key> -f samples/form/DummyApplicationForm.jpg -p form`

To process a specific image with a visualisation output created:
`python run_extract_samples.py -k <X-RapidAPI-Key> -f samples/form/DummyApplicationForm.jpg -p form --vis`

To process all images in `samples/` folder.
`python run_extract_samples.py -k <X-RapidAPI-Key> --all`

To process a specific image in japanese (notice how process-type argument is not allowed):
`python run_extract_samples.py -k <X-RapidAPI-Key> -f samples/invoice/invoice-sample-ja.png -l ja`

Samples
----------
The `/samples` directory contains sample files for processing. Running the script with the `--all` argument will
process all files in this directory. The directory is organized into subdirectories using the `process-type` as
their name - this is how the `process-type` is inferred.

Outputs
----------
The script outputs are all sent to the `outputs/` folder.

There are two outputs for every image processed:

i. `outputs/<process-type>/<filename>.json`: json output returned by DEEPREAD Extract via RapidAPI.

ii. (optional) `outputs/<process-type>/<filename>.<image extension>`: a visualisation of the processed images with
side-by-side comparison. The visualisation places all of the extracted text in the approximate location of the bounding
boxes found over a blank image. If the image requested for processing is a `pdf` the output visualisation will be
created as a `jpeg` as it needs to be converted for visualisation.
