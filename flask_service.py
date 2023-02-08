import sys
sys.path.append("/media/grartem/B7DB5B36121B73AA/Projects/SAG_MED/med-demo/normalization")
import json
import argparse
import logging

# import flask as fl
from flask import Flask, request, json, jsonify
#from flask_cors import CORS, cross_origin


import service_config

from spert.spert_trainer import SpERTTrainer
from spert.args import train_argparser, eval_argparser, predict_argparser
from spert.config_reader import process_configs, _yield_configs
from spert import input_reader
from spert.spert_trainer import SpERTTrainer
from transform_json import prepare_another_json, contextCreate_v2

from normalization.models import CADEC_SoTa
from normalization.dataset import MedNormDataset
import torch


app = Flask(__name__)

#trainer = None
#model = None
SPERT_LOADED = False
NORMALIZER_LOADED = False


@app.route('/', methods=['GET', 'POST'])
def getTextFromReactReturnJson():
    if request.method == 'POST':
        text = request.get_data().decode("utf-8")
        logging.debug("request.get_data().decode(utf-8))" + str(request.get_data().decode("utf-8")))
        with open(service_config.TEMP_FILE, 'w') as f:
            json.dump([text], f)

        for run_args, _run_config, _run_repeat in _yield_configs(arg_parser, args):
            #__predict(run_args)
            spert_trainer.predict(spert_model, dataset_path=service_config.TEMP_FILE, types_path=run_args.types_path,
                            input_reader_cls=input_reader.JsonPredictionInputReader)

        newJson = prepare_another_json(service_config.TEMP_FILE)

        if NORMALIZER_LOADED:
            mentions_ids, mentions_texts, mentions_norms = [], [], []
            for k,v in newJson["entities"].items():
                if v['MedEntityType']=="ADR" or v.get("DisType", None)=="Indication":
                    mentions_ids.append(k)
                    mentions_texts.append(v["text"])
            # ['10000002'] - какая-то заглушка у глеба, может без неё можно
            if len(mentions_texts) > 0:
                torch_ds = MedNormDataset(mentions_texts, ['10000002']*len(mentions_texts), norm_CV, use_cuda=norm_CV.use_cuda)
                dsloader = torch.utils.data.DataLoader(torch_ds, batch_size=1, shuffle=False)
                for norm_sample in dsloader:
                    inputs = norm_sample['tokenized_phrases']
                    with torch.no_grad():
                        outputs_dict = norm_net(inputs)
                        outputs_dict.label_concepless_tensors(score_treshold=6.1977e-05)
                        pred_meddra_code = norm_CV.meddra_codes[outputs_dict['output'].argmax()]
                        pred_meddra_term = norm_CV.meddra_code_to_meddra_term[pred_meddra_code]
                    mentions_norms.append(pred_meddra_term)
                for mention_id, mention_term in zip(mentions_ids, mentions_norms):
                    newJson["entities"][mention_id]["MedDRA"] = mention_term
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
    spert_trainer.predict(model, dataset_path=service_config.TEMP_FILE, types_path=run_args.types_path,
                    input_reader_cls=input_reader.JsonPredictionInputReader)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(add_help=False)
    #arg_parser.add_argument('mode', type=str, help="Mode: 'train' or 'eval'")
    args, _ = arg_parser.parse_known_args()

    arg_parser = predict_argparser()
    args, _ = arg_parser.parse_known_args()
    #try:
    for run_args, _run_config, _run_repeat in _yield_configs(arg_parser, args):
        spert_trainer = SpERTTrainer(run_args)
        spert_model = spert_trainer.load_model()
    SPERT_LOADED = True
    #except Exception as e:
    #    logging.error("Couldn't load spert model or initialize SpertTrainer: " + str(e))

    #try:
    norm_net, norm_CV = CADEC_SoTa.load_model(service_config.NORM_MODEL_DIR, return_vectorizer=True)
    # немного странное условие, надо выяснить, надо ли проверять этот флаг и вызывать функцию, или
    # можно при инициализации включить сразу нужный режим?
    # от чего вообще зависит, и какое значнеие мне надо?
    if norm_CV.use_concept_less:
        norm_CV.switch_to_regular_mode()
    if not norm_CV.use_concept_less:
        norm_CV.switch_to_concepless_mode()
    if norm_CV.use_cuda:
        norm_net.to('cuda')
    norm_net.eval()
    NORMALIZER_LOADED = True
    #except Exception as e:
    #    logging.error("Couldn't load normalization model or initialize ConceptVectorizer: " + str(e))

    if not (NORMALIZER_LOADED or SPERT_LOADED):
        raise ValueError("Both Spert and normalizer weren't initialized")

    app.run(host=service_config.SERVICE_HOST,port=service_config.SERVICE_PORT, debug=False)

#flask_cors.CORS(app, expose_headers='Authorization')
