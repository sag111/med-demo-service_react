from itertools import combinations
from collections import defaultdict
import numpy as np
import json
import re

# Парсинг выходного Json после обработки моделью spert
# в другой Json на вход в веб-интерфейс med-demo

def contextCreate_v2(test_relations, entities, connection_1, connection_0, relationPairs):
    context = {1: [], 2: [], 3: []} # первого контекста сейчас нет, только 2 и 3

    for rel in test_relations:
        h = rel["head"]
        t = rel["tail"]

        if (int(rel['type'][-1]) == 1):
            if h not in context[2] and h not in context[3]:
                context[2].append(h)
            if t not in context[2] and t not in context[3]:
                context[2].append(t)

        if (int(rel['type'][-1]) == 0):
            if h not in context[2] and h not in context[3]:
                context[3].append(h)
            if t not in context[2] and t not in context[3]:
                context[3].append(t)

    for i in range(len(context[3])):
        entitie = context[3][i]
        if connection_1.count(entitie) > 1 and connection_0.count(entitie) == 1:
            context[3].pop(i)
            context[2].append(entitie)

    for k in range(len(entities)):
        if k not in context[2] and k not in context[3]:
            context[2].append(k)  # здесь раньше заполнялся первый контекст context[1]
        elif k in context[2] and k not in context[3]:
            for el in context[3]:
                if [k, el] in relationPairs or [el, k] in relationPairs:
                    context[2].append(k)  # здесь раньше заполнялся первый контекст context[1]

    return context

def contextCreate_v3(sagnlpjson, predictions):
    """
    sagnlpjson - sagnlpjson - словарь с ключами: {text, entities}, relation нет
    predictions - выходы, которые возвращает сперт. Список словарей с ключами:
            - tokens - список строк (токенов)
            - entities - список словарей (сущностей) {type, start, end}
            - relations - список словарей (отношений) {type, head (int), tail (int)}
    """
    main_context = []
    other_context = []

    # Определяем, какое упоминание драгнейма имеет больше всего положительных связей
    drugnames_rel1_count = defaultdict(int)
    for relation in predictions["relations"]:
        if relation["type"][-1] == "1":
            first_entity = sagnlpjson["entities"][str(relation["head"])]
            second_entity = sagnlpjson["entities"][str(relation["tail"])]
            if first_entity.get("MedType") == "Drugname":
                drugnames_rel1_count[relation["head"]] += 1
            if second_entity.get("MedType") == "Drugname":
                drugnames_rel1_count[relation["tail"]] += 1
    # Оно будет в первом контексте
    main_drugname_id = sorted(list(drugnames_rel1_count.items()), reverse=True)[0][0]
    main_context.append(main_drugname_id)
    # Определяем, какие упоминания (не драгнеймы) сколько положительных и отрицательных связей они имеют
    # с драгнеймом первого контекста
    entities_posneg_rels_to_main = defaultdict(lambda: {"0": 0, "1": 0})
    for relation in predictions["relations"]:
        first_entity = sagnlpjson["entities"][str(relation["head"])]
        second_entity = sagnlpjson["entities"][str(relation["tail"])]
        if first_entity.get("MedType", None) != "Drugname":
            if relation["tail"] == main_drugname_id:
                entities_posneg_rels_to_main[relation["head"]][relation["type"][-1]] += 1
        if second_entity.get("MedType", None) != "Drugname":
            if relation["head"] == main_drugname_id:
                entities_posneg_rels_to_main[relation["tail"]][relation["type"][-1]] += 1
    # Если упоминание имеет больше положительных чем отрицательных связей с основным драгеймом,
    # то добавляем его в основной контекст, если наоборот, то во второй
    for e_i, entity in sagnlpjson["entities"].items():
        if entity.get("MedType", None) != "Drugname":
            e_i = int(e_i)
            if e_i in entities_posneg_rels_to_main.keys():
                if entities_posneg_rels_to_main[e_i]["1"] >= entities_posneg_rels_to_main[e_i]["0"]:
                    main_context.append(e_i)
                else:
                    other_context.append(e_i)
            else:
                main_context.append(e_i)
    # теперь решаем, что делать с остальными драгнеймами, если у них больше положительных связей с первым контекстом,
    # то добавляем в него
    drugnames_posneg_rels_to_main = defaultdict(lambda: {"0": 0, "1": 0})
    for relation in predictions["relations"]:
        first_entity = sagnlpjson["entities"][str(relation["head"])]
        second_entity = sagnlpjson["entities"][str(relation["tail"])]
        if first_entity.get("MedType", None) == "Drugname" and relation["head"] != main_drugname_id:
            if relation["tail"] in main_context:
                drugnames_posneg_rels_to_main[relation["head"]][relation["type"][-1]] += 1
        if second_entity.get("MedType", None) == "Drugname" and relation["tail"] != main_drugname_id:
            if relation["head"] in main_context:
                drugnames_posneg_rels_to_main[relation["tail"]][relation["type"][-1]] += 1

    for e_i, entity in sagnlpjson["entities"].items():
        if entity.get("MedType", None) == "Drugname":
            e_i = int(e_i)
            if e_i in drugnames_posneg_rels_to_main.keys():
                if drugnames_posneg_rels_to_main[e_i][1] >= drugnames_posneg_rels_to_main[e_i][0]:
                    main_context.append(e_i)
                else:
                    other_context.append(e_i)
            else:
                main_context.append(e_i)
    for e_i, entity in sagnlpjson["entities"].items():
        if int(e_i) in main_context:
            entity["Context"].append(1)
        else:
            entity["Context"].append(2)


def spert_predictions_to_sagnlpjson(spert_predictions, textlines):
    """
    params:
        spert_predictions - выходы, которые возвращает сперт. Список словарей с ключами:
            - tokens - список строк (токенов)
            - entities - список словарей (сущностей) {type, start, end}
            - relations - список словарей (отношений) {type, head (int), tail (int)}
    """

    resultFormat = {}
    num = 1
    # получаем данные выходного файла предсказаний модели spert в формате Json
    #with open(tmpFilePath) as f:
    #    file_content = f.read()
    #    sagnlpjson = json.loads(file_content)

    template = spert_predictions[0]

    # формируем поля в результирующем Json: text_id, text
    # resultFormat['text_id'] = re.findall(r"\d+", template['tokens'][0])[0]
    resultFormat['text'] = ' '.join(template['tokens'])
    resultFormat['entities'] = {}
    countItem = 0
    ileft = 0


    relationPairs = []
    relationIndexes = []
    relationUnique = []

    connection_1 = []
    connection_0 = []

    # подготовка списков для входа в функцию contextCreate:
    # relationPairs: список с парами индексов сущностей, которые есть в поле relations
    # relationUnique: список с уникальными (без повторов) индексами всех сущностей, состоящими в relations
    #print(template['relations'])
    for rel in template['relations']:
        if (int(rel['type'][-1]) == 1):
            relationPairs.append([rel['head'], rel['tail']])
            connection_1.append(rel['head'])
            connection_1.append(rel['tail'])
        if (int(rel['type'][-1]) == 0):
            connection_0.append(rel['head'])
            connection_0.append(rel['tail'])

    for pair in relationPairs:
        relationIndexes += tuple(pair)

    [relationUnique.append(i) for i in relationIndexes if i not in relationUnique]

    # формируем контексты функцией contextCreate
    context = {}
    # context = contextCreate(relationPairs, relationUnique)
    context = contextCreate_v2(template['relations'], template['entities'], connection_1, connection_0, relationPairs)


    # для каждой entitie формируем нужные поля:
    # spans, MedEntitieType, (MedType, DisType - если есть), Context

    for item in template['entities']:
        resultFormat['entities'][countItem] = {}
        resultItem = resultFormat['entities'][countItem]

        substrLeft = template['tokens'][item['start']]
        substrRight = template['tokens'][item['end']-1]

        indexLeftStart = resultFormat['text'].find(substrLeft, ileft)
        ileft = indexLeftStart
        indexRightEnd = resultFormat['text'].find(substrRight, ileft)+ len(substrRight)

        resultItem['text'] = " ".join(template['tokens'][x] for x in [i for i in range(int(item['start']), int(item['end']))])
        resultItem['spans'] = [{"begin": indexLeftStart, "end": indexRightEnd}]
        resultItem['MedEntityType'] = item['type'].split(':')[0]
        if ':' in item['type']:
            typeKeyValue = item['type'].split(':')[1]
            itemType = typeKeyValue.split('Type')[0] + 'Type'
            itemTypeValue = typeKeyValue.split('Type')[1]
            resultItem[itemType] = itemTypeValue

        resultFormat['entities'][countItem]['Context'] = []

        for k, v in context.items():
            if countItem in v:
                resultFormat['entities'][countItem]['Context'].append(str(k))

        countItem += 1

    return resultFormat

def spert_predictions_to_sagnlpjson_2(spert_predictions, textlines):
    """
    params:
        spert_predictions - выходы, которые возвращает сперт. Список словарей с ключами:
            - tokens - список строк (токенов)
            - entities - список словарей (сущностей) {type, start, end}
            - relations - список словарей (отношений) {type, head (int), tail (int)}
    """

    sagnlpjson = {}
    # сейчас работаем с одним предсказанием за раз
    prediction = spert_predictions[0]
    textline = textlines[0]

    # формируем поля в результирующем Json: text_id, text
    # resultFormat['text_id'] = re.findall(r"\d+", template['tokens'][0])[0]

    # получаем позиции токенов, пробуем из исходного текста, если не вышло, то из сконкатенированных токенов
    try:
        sagnlpjson['text'] = textline
        tokens_positions = []
        current_pos = 0
        for t in prediction["tokens"]:
            pattern = re.compile(t)
            mo = pattern.search(textline, pos=current_pos)
            tokens_positions.append((mo.start(), mo.end()))
            current_pos = mo.end()
    except:
        sagnlpjson['text'] = ""
        tokens_positions = []
        for t in prediction["tokens"]:
            start = len(sagnlpjson['text'])
            sagnlpjson['text'] += t
            end = start + len(t)
            sagnlpjson['text'] += " "
            tokens_positions.append((start, end))
        sagnlpjson['text'] = sagnlpjson['text'][:-1]

    # приводим сущности в формат sagnlpjson, не заполняя контексты
    sagnlpjson['entities'] = {}
    for e_i, entity in enumerate(prediction['entities']):
        new_entity = {}
        startToken = tokens_positions[entity['start']]
        endToken = tokens_positions[entity['end']]  # -1?
        new_entity['text'] = sagnlpjson['text'][startToken[0]:endToken[1]]
        new_entity['spans'] = [{"begin": startToken[0], "end": endToken[1]}]
        new_entity['MedEntityType'] = entity['type'].split(':')[0]
        if ':' in entity['type']:
            typeKeyValue = entity['type'].split(':')[1]
            itemType = typeKeyValue.split('Type')[0] + 'Type'
            itemTypeValue = typeKeyValue.split('Type')[1]
            new_entity[itemType] = itemTypeValue
        new_entity['Context'] = []
        sagnlpjson['entities'][str(e_i)] = new_entity

    # заполняем контексты в сущностях по связям
    contextCreate_v3(sagnlpjson, prediction)
    return sagnlpjson