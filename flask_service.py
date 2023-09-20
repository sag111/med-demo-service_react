import os
import sys
# Это нужно так как у сохранённой модели глеба зашиты пути к его модулям. ВОт почему надо сохранять state_dict, а не всю модель целиком, если делаем кастомные модули.
sys.path.append(os.getcwd() + '/normalization')
import json
import argparse
import logging
import random

# import flask as fl
from flask import Flask, request, json, jsonify
#from flask_cors import CORS, cross_origin


import service_config

from spert.spert_trainer import SpERTTrainer
from spert.args import train_argparser, eval_argparser, predict_argparser
from spert.config_reader import _yield_configs
from spert import input_reader
from spert.spert_trainer import SpERTTrainer
from transform_json import spert_predictions_to_sagnlpjson, spert_predictions_to_sagnlpjson_2

from normalization.models import CADEC_SoTa
from normalization.dataset import MedNormDataset
import torch

IS_DEBUG_WITHOUT_SERVICE = False

app = Flask(__name__)

#trainer = None
#model = None
SPERT_LOADED = False
NORMALIZER_LOADED = False

def ParseText(textline):
    """
    Функция получает строку с текстом, отправляет в сперт, делает постобработку и получает sagnlp с сущностями и связями
    """

    predictions = spert_trainer.predict(spert_model, textlines_list=[textline],
                          input_reader_cls=input_reader.ListOfStringsPredictionInputReader)
    print("PREDICTIONS", predictions)
    newJson = spert_predictions_to_sagnlpjson(predictions, [textline])
    return newJson

def NormalizeSagnlpjson(sagnlpjson):
    """
    Функция принимает sagnlpjson, ищет в нём сущности для нормализации и нормализует моделью.
    Функция изменяет сам json, поэтому возвращаемое значение - это тот же объект
    """
    mentions_ids, mentions_texts, mentions_norms = [], [], []
    for k, v in sagnlpjson["entities"].items():
        if v['MedEntityType'] == "ADR" or v.get("DisType", None) == "Indication":
            mentions_ids.append(k)
            mentions_texts.append(v["text"])
    # ['10000002'] - какая-то заглушка у глеба, может без неё можно
    if len(mentions_texts) > 0:
        torch_ds = MedNormDataset(mentions_texts, ['10000002'] * len(mentions_texts), norm_CV,
                                  use_cuda=norm_CV.use_cuda)
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
            sagnlpjson["entities"][mention_id]["MedDRA"] = mention_term
    return sagnlpjson

@app.route('/', methods=['GET', 'POST'])
def hello():
    return "This is web-service that parse russian texts, extract pharmaceptical entities from it and normalize them " \
           "according to MedDRA 24.1<br>" \
           "send get request to the url /json_test to get example of returning json format;<br>" \
           "send get request to the url /models_status to check if models are loaded and ready; <br>" \
           "send post request with text data to the url /process to parse input text and receive json"

@app.route('/get_example', methods=['GET'])
def json_test():
    with open("data/example.json", "r") as f:
        examples_list = json.load(f)
    random_example = examples_list[random.randint(0, len(examples_list)-1)]
    response = jsonify({'data': random_example})
    return response

@app.route('/models_status', methods=['GET'])
def models_status():
    return jsonify({"data": {"NER model loaded": SPERT_LOADED, "Normalization model loaded": NORMALIZER_LOADED}})

# очереди?

@app.route('/process', methods=['GET', 'POST'])
def getTextFromReactReturnJson():
    if request.method == 'POST':
        text = request.get_data().decode("utf-8")
        logging.debug("request.get_data().decode(utf-8))" + str(request.get_data().decode("utf-8")))
        sagnlpjson = ParseText(text)

        if NORMALIZER_LOADED:
            NormalizeSagnlpjson(sagnlpjson)
        response = jsonify({'data': sagnlpjson})
        #response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    else:
        print(request)
        return request.get_data()

if __name__ == '__main__':
    #arg_parser = argparse.ArgumentParser(add_help=False)
    #arg_parser.add_argument('mode', type=str, help="Mode: 'train' or 'eval'")
    #args, _ = arg_parser.parse_known_args()

    spert_arg_parser = predict_argparser()
    spert_args, _ = spert_arg_parser.parse_known_args(["--config", service_config.SPERT_CONFIG_PATH])
    for run_args, _run_config, _run_repeat in _yield_configs(spert_arg_parser, spert_args):

        spert_trainer = SpERTTrainer(run_args)
        spert_model = spert_trainer.load_model()
        break
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

    # Отладка функций
    if IS_DEBUG_WITHOUT_SERVICE:
        # "я принял аспирин от боли в голове, но от него у меня заболел живот, начало рвать и прочие побочки. .."
        sagnlpjson = ParseText("Я выпил аспирин, чтоб голова не болела, но от него у меня заболел живот.От ношпы обычно не болел, но она мне не помогала.")
        #sagnlpjson = ParseText("я принял аспирин от боли в голове, но от него у меня заболел живот, начало рвать и прочие побочки. ..")
        if NORMALIZER_LOADED:
            NormalizeSagnlpjson(sagnlpjson)
        response = {'data': sagnlpjson}
        print(response)

    # Запуск сервиса
    else:
        app.run(host=service_config.SERVICE_HOST, port=service_config.SERVICE_PORT, debug=False, threaded=False)

#flask_cors.CORS(app, expose_headers='Authorization')
