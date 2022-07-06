import argparse
import json
import mimetypes
import os
import cv2
import numpy
import requests
import os
import itertools
from PIL import Image
from pdf2image import convert_from_path
from bounding_box import bounding_box as bb


OUTPUT_DIR = 'outputs'
SAMPLES_DIR = 'samples'

LANGUAGES = ('en', 'ja')
ALL_PROCESS_TYPES = ('form', 'invoice', 'receipt')

PROCESS_TYPES = {
    'en': ALL_PROCESS_TYPES,
    'ja': ('invoice',)
}

HOSTS = {
    'en': 'deepread-extract-intelligent-document-extraction.p.rapidapi.com',
    'ja': 'deepread-extract-intelligent-invoice-extraction-japanese.p.rapidapi.com'
}


def visualise_ocr(data, original_image, language, process_type):
    """
    Visualise DEEPREAD Extract response in side-by-side image comparison.
    """
    if process_type == 'form':
        return visualise_form(data, original_image, language)
    else:
        return visualise_preset(data, original_image, language)

def visualise_form(data, original_image, language):
    extracted_data  =  data['pages'][0]['extractedInformation']
    colours = itertools.cycle(['navy', 'blue', 'aqua', 'teal', 'olive', 'green', 'lime', 'yellow', 'orange', 'red', 'maroon', 'fuchsia', 'purple', 'black', 'gray', 'silver'])
    vis_image = cv2.cvtColor(numpy.array(original_image.convert("RGB")), cv2.COLOR_BGR2RGB)
    for pair, colour in zip(extracted_data, colours):
        coords = pair['key']['bounding_box']
        bb.add(vis_image, coords[0], coords[1], coords[2], coords[3], 'key', colour)
        if pair['value'] is not None:
            coords = pair['value']['bounding_box']
            bb.add(vis_image, coords[0], coords[1], coords[2], coords[3], 'value', colour)
    return vis_image

def visualise_preset(data, original_image, language):
    extracted_data  =  data['pages'][0]['extractedInformation']
    vis_image = cv2.cvtColor(numpy.array(original_image.convert("RGB")), cv2.COLOR_BGR2RGB)
    for key in extracted_data['fields'].keys():
        coords = extracted_data['fields'][key]['bounding_box']
        bb.add(vis_image, coords[0], coords[1], coords[2], coords[3], key, 'red')
    return vis_image


def process_file(filename, language, key, process_type, visualise):
    """
    Process image with DEEPREAD Extract RapidAPI endpoint outputting visualisation.
    """
    print(f'Processing file {filename} as {process_type}')

    host = HOSTS[language]
    url = f'https://{host}/api/v1/extract'
    print(f'Processing with url {url}.')

    headers = {
        'X-RapidAPI-Host': host,
    	'X-RapidAPI-Key': key
    }

    with open(filename, 'rb') as file_bytes:
        payload = {
            'source_file': (
                'source_file{}'.format(os.path.splitext(filename)[1]),
                file_bytes,
                mimetypes.guess_type(filename)[0]
            )
        }
        params = {'process_type': process_type} if language == 'en' else {}
        response = requests.post(url, data=params, files=payload, headers=headers)

    content = response.text

    try:
        data = json.loads(content)['data']
    except KeyError:
        print(f'Failed to process document {filename}: {content}')
        return

    output_path = os.path.join(OUTPUT_DIR, process_type)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    json_filename = os.path.join(output_path, '{}.json'.format(os.path.splitext(os.path.basename(filename))[0]))
    with open(json_filename, 'w') as json_file:
        json_file.write(content)

    if visualise:
        print('Creating visualisation for {}'.format(filename))
        if '.pdf' in filename:
            pages = convert_from_path(filename, 250, single_file=True)
            new_filename = filename.replace('.pdf', '.jpg')
            pages[0].save(new_filename, 'JPEG')
            filename = new_filename
        with Image.open(filename) as original_image:
            output_image = visualise_ocr(data, original_image, language, process_type)
            cv2.imwrite(os.path.join(output_path, os.path.basename(filename)), output_image)


def find_language(filename, language=None):
    """
    Determines language for processing.

    Order of preference:
    1. Provided via command line --language
    2. Contained in filename via '<name>-<language>.<ext>'
    3. Default 'en'
    """
    if language:
        return language

    name = os.path.splitext(os.path.basename(filename))[0]
    for language in LANGUAGES:
        if name.endswith(f'-{language}'):
            return language

    return 'en'


def find_process_types(language=None):
    if language is None:
        return ALL_PROCESS_TYPES
    return PROCESS_TYPES[language]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files with DEEPREAD Extract.')
    parser.add_argument('-k', '--key', type=str, required=True,
                        help='X-RapidAPI-Key header required to access RapidAPI.')
    parser.add_argument('-l', '--language', type=str, default=None,
                        help='language to determine which RapidAPI endpoint to call.'
                             'ACCEPT-LANGUAGE value passed DEEPREAD.')
    parser.add_argument('-p', '--process-type', type=str, default=None, choices=ALL_PROCESS_TYPES,
                        help=f'determines which document you will process in the DEEPREAD Extract Solution.')
    parser.add_argument('--vis', '--visualise', dest='visualise', action='store_true',
                        default=False,
                        help='create visualisation output?')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', type=str, help='path the file to process')
    group.add_argument('--all', dest='all', action='store_true',
                        default=False,
                        help='process all files in samples/ directory?')

    args = parser.parse_args()

    if args.all and args.process_type:
        parser.error("--process-type argument not allowed with --all")

    if args.file:
        language = find_language(args.file, args.language)
        process_type = args.process_type
        if args.language == 'ja':
            if process_type:
                parser.error("--process-type argument not allowed with language ja")
            process_type = 'invoice'
        elif process_type is None:
            parser.error("--file requires --process-type when language is en.")

        process_file(args.file, language, args.key, process_type, args.visualise)
    else:
        process_types = find_process_types(args.language)
        for sample_content in os.listdir(SAMPLES_DIR):
            if not (os.path.isdir(os.path.join(SAMPLES_DIR, sample_content)) and sample_content in process_types):
                continue
            process_type = sample_content
            process_type_dir = os.path.join(SAMPLES_DIR, sample_content)
            for sample in os.listdir(process_type_dir):
                language = find_language(sample, args.language)
                process_file(os.path.join(process_type_dir, sample), language, args.key, process_type, args.visualise)
