from spert.spert_trainer import SpERTTrainer

# import flask as fl
from flask import Flask, request, json, jsonify
from flask_cors import CORS, cross_origin

import argparse
import json

from args import train_argparser, eval_argparser, predict_argparser
from config_reader import process_configs
from spert import input_reader
from spert.spert_trainer import SpERTTrainer
from config_reader import _yield_configs
from transform_json import prepare_another_json, contextCreate_v2
import logging
app = Flask(__name__)

#trainer = None
#model = None

def __load_model(run_args):
    global model
    global trainer

    trainer = SpERTTrainer(run_args)
    model = trainer.load_model()

@app.route('/', methods=['GET', 'POST'])
def getTextFromReactReturnJson():
    if request.method == 'POST':
        text = request.get_data().decode("utf-8")
        logging.debug("request.get_data().decode(utf-8))" + str(request.get_data().decode("utf-8")))
        with open('predicts/input_prediction_example_1.json', 'w') as f:
            json.dump([text], f)

        for run_args, _run_config, _run_repeat in _yield_configs(arg_parser, args):
            #__predict(run_args)
            trainer.predict(model, dataset_path=run_args.dataset_path, types_path=run_args.types_path,
                            input_reader_cls=input_reader.JsonPredictionInputReader)

        newJson = prepare_another_json()
        response = jsonify({'data': newJson})
        #response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    else:
        print(request)
        return request.get_data()

'''
def _predict(target):
    arg_parser = predict_argparser()
    process_configs(target=target, arg_parser=arg_parser)
'''

def __predict(run_args):
    #global model
    #global trainer
    #trainer = SpERTTrainer(run_args)
    #model = trainer.load_model()
    trainer.predict(model, dataset_path=run_args.dataset_path, types_path=run_args.types_path,
                    input_reader_cls=input_reader.JsonPredictionInputReader)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('mode', type=str, help="Mode: 'train' or 'eval'")
    args, _ = arg_parser.parse_known_args()

    arg_parser = predict_argparser()
    args, _ = arg_parser.parse_known_args()
    for run_args, _run_config, _run_repeat in _yield_configs(arg_parser, args):
        trainer = SpERTTrainer(run_args)
        model = trainer.load_model()

    #app.run(host='194.87.237.6', port=8081, debug=False)
    app.run(port=8081, debug=False)
    #app.run(host='127.0.0.1', port=3000, threaded = True, debug=True)

#flask_cors.CORS(app, expose_headers='Authorization')
