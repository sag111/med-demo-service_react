import argparse as ap
import logging
import pandas as pd
from typing import List, Tuple, Dict
from sklearn.metrics import precision_recall_fscore_support as prfs
import json

def _convert_by_setting(gt:List[List[Tuple]], pred:List[List[Tuple]], include_entity_types:bool=True):
    assert len(gt) == len(pred)

    # either include or remove entity types based on setting
    def convert(t):
        if not include_entity_types:
            # remove entity type and score for evaluation
            if type(t[0]) == str:  # entity
                c = [t[0], t[1], 'pseudo_entity_type']
            else:  # relation
                c = [(t[0][0], t[0][1], 'pseudo_entity_type'),
                     (t[1][0], t[1][1], 'pseudo_entity_type'), t[2]]
        else:
            c = list(t[:3])
        return tuple(c)

    converted_gt, converted_pred = [], []
    for sample_gt, sample_pred in zip(gt, pred):
        converted_gt.append([convert(t) for t in sample_gt])
        converted_pred.append([convert(t) for t in sample_pred])

    return converted_gt, converted_pred

def _score(gt:List[List[Tuple]], pred:List[List[Tuple]]):
    assert len(gt) == len(pred)

    gt_flat = []
    pred_flat = []
    types = set()

    for (sample_gt, sample_pred) in zip(gt, pred):
        union = set()
        union.update(sample_gt)
        union.update(sample_pred)

        for s in union:
            if s in sample_gt:
                t = s[2]
                gt_flat.append(t)
                types.add(t)
            else:
                gt_flat.append(0)

            if s in sample_pred:
                t = s[2]
                pred_flat.append(t)
                types.add(t)
            else:
                pred_flat.append(0)
                
    return gt_flat, pred_flat, types

def _compute_metrics(gt_all, pred_all, types, print_results:bool=False):
    labels = list(types)
    per_type = prfs(gt_all, pred_all, labels=labels, average=None, zero_division=0)
    micro = prfs(gt_all, pred_all, labels=labels, average='micro', zero_division=0)[:-1]

    macro = prfs(gt_all, pred_all, labels=labels, average='macro', zero_division=0)[:-1]
    total_support = sum(per_type[-1])

    if print_results:
        res_str = _print_results(per_type, list(micro) + [total_support], list(macro) + [total_support], types)

    return res_str

def _get_row(data, label):
    row = [label]
    for i in range(len(data) - 1):
        row.append("%.2f" % (data[i] * 100))
    row.append(data[3])
    return tuple(row)

def _print_results(per_type:List, micro:List, macro:List, types:List):
    columns = ('type', 'precision', 'recall', 'f1-score', 'support')

    row_fmt = "%20s" + (" %12s" * (len(columns) - 1))
    results = [row_fmt % columns, '\n']

    metrics_per_type = []
    for i, t in enumerate(types):
        metrics = []
        for j in range(len(per_type)):
            metrics.append(per_type[j][i])
        metrics_per_type.append(metrics)

    for m, t in zip(metrics_per_type, types):
        results.append(row_fmt % _get_row(m, t))
        results.append('\n')

    results.append('\n')

    # micro
    results.append(row_fmt % _get_row(micro, 'micro'))
    results.append('\n')

    # macro
    results.append(row_fmt % _get_row(macro, 'macro'))

    results_str = ''.join(results)
    print(results_str)
    
    return results_str

def read_json(path_to_df: str):
    _gt_entities = []
    _gt_relations = []
    with open(path_to_df) as f:
        df = json.load(f)
    for s in df:
        sample_gt_entities = []
        for _, ent in s['entities'].items():
            try:
                ent['tag'][0]
            except:
                continue
            if ent['tag'][0] == 'Note':
                continue
            sample = (';'.join([str(i['begin']) for i in ent['spans']]), 
                      ';'.join([str(i['end']) for i in ent['spans']]), 
                      ent['tag'][0])
            sample_gt_entities.append(sample)
        _gt_entities.append(sample_gt_entities)

        sample_gt_relations = []
        if 'relations' not in s.keys():
            s['relations'] = []
        for rel in s['relations']:
            ent_1 = (';'.join([str(i['begin']) for i in rel['first_entity']['spans']]), 
                     ';'.join([str(i['end']) for i in rel['first_entity']['spans']]), 
                     rel['first_entity']['tag'][0])
            ent_2 = (';'.join([str(i['begin']) for i in rel['second_entity']['spans']]), 
                     ';'.join([str(i['end']) for i in rel['second_entity']['spans']]), 
                     rel['second_entity']['tag'][0])
            
            if ("relation_class" in rel) and not (("_0" in rel["relation_type"]) or ("_1" in rel["relation_type"])):
                rel_type = rel['relation_type']+"_"+str(rel["relation_class"])
            else:
                rel_type = rel['relation_type']
                
            if rel_type is None or rel_type == 'null':
                rel_type = 'null'
                #continue
            sample_gt_relations.append((ent_1, ent_2, rel_type))
        _gt_relations.append(sample_gt_relations)
        
    return _gt_entities, _gt_relations

def compute_scores(gt_ent, pred_ent, gt_rel, pred_rel, log=None):
    print("Evaluation")

    print("")
    print("--- Entities (named entity recognition (NER)) ---")
    print("An entity is considered correct if the entity type and span is predicted correctly")
    print("")
    gt, pred = _convert_by_setting(gt_ent, pred_ent, include_entity_types=True)
    gt_flat, pred_flat, types = _score(gt, pred)
    ner_eval = _compute_metrics(gt_flat, pred_flat, types, print_results=True)
    
    print("")
    print("--- Relations ---")
    print("")
    print("Without named entity classification (NEC)")
    print("A relation is considered correct if the relation type and the spans of the two "
          "related entities are predicted correctly (entity type is not considered)")
    print("")
    gt, pred = _convert_by_setting(gt_rel, pred_rel, include_entity_types=False)
    #print('gt')
    #print(gt[10])
    #print('pred')
    #print(pred[10])
    gt_flat, pred_flat, types = _score(gt, pred)
    #print('gt_flat')
    #print(gt_flat[:5])
    #print('pred_flat')
    #print(pred_flat[:5])
    rel_eval = _compute_metrics(gt_flat, pred_flat, types, print_results=True)
    
    print("")
    print("With named entity classification (NEC)")
    print("A relation is considered correct if the relation type and the two "
          "related entities are predicted correctly (in span and entity type)")
    print("")
    gt, pred = _convert_by_setting(gt_rel, pred_rel, include_entity_types=True)

    gt_flat, pred_flat, types = _score(gt, pred)
    rel_nec_eval = _compute_metrics(gt_flat, pred_flat, types, print_results=True)
    
    if log:
        log.info('Evaluation:')
        log.info('\n--- Entities (named entity recognition (NER)) ---')
        log.info(f'{ner_eval}')
        log.info('\n--- Relations (Without named entity classification (NEC)) ---')
        log.info(f'{rel_eval}')
        log.info('\n--- Relations (With named entity classification (NEC)) ---')
        log.info(f'{rel_nec_eval}')

if __name__ == "__main__":
    args_parser = ap.ArgumentParser()
    args_parser.add_argument("-t", dest="true", default="./true.json", type=str, 
                             help="Path to the gold-true labels in JSON format file (default: 'true.json')")
    args_parser.add_argument("-p", dest="pred", default="./pred.json", type=str, 
                             help="Path to the predicted labels in JSON format file (default: 'pred.json')")
    args_parser.add_argument("-o", dest="output_path", default="./", type=str,
                             help="Path to store output log (default: './')")
    args = args_parser.parse_args()
    
    logging.basicConfig(format = u'%(message)s', filemode='w', level = logging.INFO, 
                        filename = args.output_path+"output_log.txt")
    
    print(f"Parse data from {args.true}")
    gt_ent, gt_rel = read_json(args.true)
    
    print(f"Parse data from {args.pred}\n")
    pred_ent, pred_rel = read_json(args.pred)
    
    compute_scores(gt_ent, pred_ent, gt_rel, pred_rel, log=logging)
    
    logging.info('\nSuccessful end.')