from itertools import combinations
import numpy as np
import json
import re

# Парсинг выходного Json после обработки моделью spert
# в другой Json на вход в веб-интерфейс med-demo

def contextCreate_v2(test_relations, entities, connection_1, connection_0, relationPairs):
    context = {1: [], 2: [], 3: []}

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
            context[1].append(k)
        elif k in context[2] and k not in context[3]:
            for el in context[3]:
                if [k, el] in relationPairs or [el, k] in relationPairs:
                    context[1].append(k)

    return context

def prepare_another_json():

    resultFormat = {}
    num = 1
    # получаем данные выходного файла предсказаний модели spert в формате Json
    with open('predicts/output_predictions_1.json') as f:
        file_content = f.read()
        templates = json.loads(file_content)

    template = templates[0]

    # формируем поля в результирующем Json: text_id, text
    resultFormat['text_id'] = re.findall(r"\d+", template['tokens'][0])[0]
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
    print('????????????')
    print(template['relations'])
    print('------------')
    print(template['entities'])
    print('????????????')
    context = contextCreate_v2(template['relations'], template['entities'], connection_1, connection_0, relationPairs)


    # для каждой entitie формируем нужные поля:
    # spans, MedEntitieType, (MedType, DisType - если есть), Context

    for item in template['entities']:
        resultFormat['entities'][countItem] = {}
        resultItem = resultFormat['entities'][countItem]

        substrLeft = template['tokens'][item['start']]
        substrRight = template['tokens'][item['end']]

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
